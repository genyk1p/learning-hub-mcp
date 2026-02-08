# Learning Hub: нативный плагин для OpenClaw (Bridge)

## Зачем это нужно

### Текущая проблема

Learning Hub MCP — это Python MCP-сервер, который хранит домашки, оценки, предметы и бонусные задания для трекинга учёбы ребёнка. Как MCP-сервер он работает корректно.

Проблема в том, что **OpenClaw** (AI-гейтвей) не поддерживает MCP-серверы нативно. В `openclaw.json` нет секции `mcpServers`. Сейчас используется костыль:

```
Агент вызывает exec → запускает `npx mcporter call learning-hub.list_subjects` → парсит stdout
```

Почему это плохо:

1. **Модель не знает что Learning Hub существует** — его нет в tool list модели. Модель узнаёт о нём только из текстовых инструкций в `USER.md`. При сбросе контекста или compaction модель «забывает» и уходит в fallback «пришли скрин».
2. **В mcporter баг** — когда MCP-инструмент возвращает список, `mcporter call` (default/json формат) рендерит только первый элемент. `list_subjects` возвращает 1 предмет вместо 7. Из-за этого модель не смогла сопоставить `subject_id=5` с названием предмета.
3. **Каждый вызов ~3 секунды** — запуск Node.js, подключение к MCP по STDIO, вызов, выход. 20 вызовов = минута ожидания.
4. **Модель не знает схему** — не знает какие инструменты есть и какие аргументы принимают. Вынуждена узнавать это в рантайме через `mcporter list --schema`, тратя токены и вызовы.

### Решение

Написать тонкий **OpenClaw-плагин** (TypeScript), который работает как мост:

- При старте подключается к Python MCP-серверу через STDIO
- Узнаёт список всех tools через MCP-протокол
- Регистрирует каждый tool как нативный agent tool через `api.registerTool()`
- Проксирует вызовы: модель вызывает tool нативно → плагин пересылает в MCP-сервер → возвращает результат

После этого модель видит `learning_hub_list_subjects`, `learning_hub_list_grades` и т.д. **прямо в своём tool list**, наравне с `read`, `write`, `exec`.

### Для кого

- **OpenClaw-агент «Emma»** — семейный ассистент на домашнем сервере
- **Конечные пользователи**: семья (родители, ребёнок, родственники), общаются через Telegram
- Ребёнок (Стас) спрашивает про домашку/оценки в Telegram DM → агент должен мгновенно запросить Learning Hub без exec/mcporter

---

## Техническое задание

### Архитектура

```
┌─────────────────────────────────────────────────┐
│  OpenClaw Gateway (Node.js)                     │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │  learning-hub-bridge плагин (TypeScript)  │  │
│  │                                           │  │
│  │  - Запускает Python MCP-сервер по STDIO   │  │
│  │  - Читает список tools через MCP-протокол │  │
│  │  - Регистрирует каждый как registerTool() │  │
│  │  - Проксирует execute() → MCP callTool()  │  │
│  └──────────────┬────────────────────────────┘  │
│                 │ STDIO (stdin/stdout)           │
│  ┌──────────────▼────────────────────────────┐  │
│  │  learning-hub-mcp (Python, FastMCP)       │  │
│  │  - SQLite база данных                     │  │
│  │  - 39 инструментов                        │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  Tool list модели:                              │
│  ✅ read, write, exec, ...                      │
│  ✅ learning_hub_list_subjects     ← НОВЫЙ      │
│  ✅ learning_hub_list_grades       ← НОВЫЙ      │
│  ✅ learning_hub_list_homeworks    ← НОВЫЙ      │
│  ✅ ... (все 39 инструментов)                   │
└─────────────────────────────────────────────────┘
```

### Стек технологий

- **Язык**: TypeScript (плагины OpenClaw обязаны быть на TypeScript, загружаются через jiti)
- **MCP-клиент**: `@modelcontextprotocol/sdk` — официальный MCP TypeScript SDK
  - `StdioClientTransport` — запуск и коммуникация с Python MCP-сервером
  - `Client.listTools()` — обнаружение инструментов
  - `Client.callTool()` — проксирование вызовов
- **Схема**: `@sinclair/typebox` для JSON Schema (конвенция OpenClaw) — или прокинуть `inputSchema` из MCP-инструмента напрямую
- **Манифест плагина**: `openclaw.plugin.json`

### Структура плагина

```
learning-hub-bridge/
├── openclaw.plugin.json       # Манифест плагина
├── index.ts                   # Точка входа
├── package.json               # Зависимости
└── README.md                  # Как подключить к OpenClaw
```

### Манифест (`openclaw.plugin.json`)

```json
{
  "id": "learning-hub",
  "configSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "command": {
        "type": "string",
        "description": "Команда запуска MCP-сервера"
      },
      "cwd": {
        "type": "string",
        "description": "Рабочая директория для процесса MCP-сервера"
      },
      "toolPrefix": {
        "type": "string",
        "default": "learning_hub",
        "description": "Префикс имён инструментов (например learning_hub_list_subjects)"
      }
    }
  }
}
```

### Точка входа (`index.ts`)

Псевдокод / структура:

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

export default function (api) {
  const config = api.config;

  const command = config?.command ?? "/bin/bash";
  const args = config?.args
    ?? ["-lc", "cd /home/eva/.openclaw/workspace/learning-hub-mcp && exec .venv/bin/learning-hub-mcp"];
  const cwd = config?.cwd
    ?? "/home/eva/.openclaw/workspace/learning-hub-mcp";
  const toolPrefix = config?.toolPrefix ?? "learning_hub";

  // 1. Создать MCP-клиент с STDIO-транспортом
  const transport = new StdioClientTransport({ command, args, cwd });
  const client = new Client({ name: "learning-hub-bridge", version: "1.0.0" });

  // 2. Подключиться и обнаружить инструменты
  const toolsReady = (async () => {
    await client.connect(transport);
    const { tools } = await client.listTools();

    // 3. Зарегистрировать каждый MCP-инструмент как нативный agent tool
    for (const tool of tools) {
      const toolName = `${toolPrefix}_${tool.name}`;

      api.registerTool({
        name: toolName,
        description: tool.description ?? `Learning Hub: ${tool.name}`,
        parameters: tool.inputSchema ?? { type: "object", properties: {} },

        async execute(_id, params) {
          // 4. Проксировать вызов в MCP-сервер
          const result = await client.callTool({
            name: tool.name,
            arguments: params,
          });

          // 5. Собрать множественные TextContent блоки в один JSON-массив
          //    (FastMCP сериализует list[Model] как отдельные TextContent на каждый элемент)
          const texts = (result.content ?? [])
            .filter(b => b.type === "text")
            .map(b => b.text);

          if (texts.length > 1) {
            try {
              const parsed = texts.map(t => JSON.parse(t));
              return {
                content: [{ type: "text", text: JSON.stringify(parsed, null, 2) }]
              };
            } catch { /* если не парсится — прокинуть как есть */ }
          }

          return { content: result.content };
        },
      });
    }
  })();

  // Очистка при остановке gateway
  api.onShutdown?.(() => {
    client.close();
  });
}
```

### Важные детали реализации

1. **Именование tools**: MCP-инструменты называются `list_subjects`, `list_grades` и т.д. В OpenClaw добавляем префикс для избежания коллизий: `learning_hub_list_subjects`. Префикс настраивается через конфиг.

2. **Формат content blocks**: MCP `CallToolResult.content` — это массив `{type: "text", text: "..."}`. OpenClaw `execute()` возвращает тот же формат. Они совместимы — можно прокидывать напрямую.

3. **Проблема сериализации массивов**: Python MCP-сервер (FastMCP) сериализует `list[Model]` как **несколько отдельных TextContent блоков** (по одному на элемент). Это вызывало баг mcporter. В bridge-плагине нужно собирать их в один JSON-массив (см. код выше в execute).

4. **Ленивое подключение**: рассмотреть подключение к MCP-серверу лениво (при первом вызове), а не при инициализации плагина, чтобы не блокировать старт gateway если Python-сервер стартует медленно.

5. **Переподключение**: если Python-процесс падает, bridge должен обнаружить это и перезапустить. Обернуть `callTool` в try/catch с логикой реконнекта.

6. **optional: true**: регистрировать tools с `{ optional: true }`, чтобы их можно было добавить в allowlist конкретного агента. Это конвенция OpenClaw для не-core инструментов.

### Текущие инструменты MCP-сервера (39 штук)

Все должны быть зарегистрированы:

**Предметы**: `create_subject`, `list_subjects`, `update_subject`
**Темы предметов**: `create_subject_topic`, `list_subject_topics`, `update_subject_topic`
**Оценки**: `add_grade`, `list_grades`, `update_grade`
**Домашки**: `create_homework`, `list_homeworks`, `update_homework`, `complete_homework`
**Бонусные задания**: `create_bonus_task`, `list_bonus_tasks`, `update_bonus_task`, `apply_bonus_task_result`
**Недели**: `create_week`, `get_week`, `list_weeks`, `update_week`, `finalize_week`
**Бонусный фонд**: `create_bonus_fund`, `get_bonus_fund`, `list_bonus_funds`, `update_bonus_fund`
**Обзоры тем**: `create_topic_review`, `list_topic_reviews`, `update_topic_review`
**Книги**: `create_book`, `list_books`, `update_book`
**Синхронизация EduPage**: `sync_edupage_homeworks`, `sync_edupage_grades`

---

## Как подключить к OpenClaw

### Шаг 1: Разместить плагин

```bash
# Вариант A: Установка через CLI
openclaw plugins install ./learning-hub-bridge

# Вариант B: Симлинк для разработки
openclaw plugins install -l ./learning-hub-bridge

# Вариант C: Ручное размещение
cp -r learning-hub-bridge ~/.openclaw/extensions/learning-hub
```

### Шаг 2: Включить плагин и настроить в `openclaw.json`

```json
{
  "plugins": {
    "entries": {
      "learning-hub": {
        "enabled": true,
        "command": "/bin/bash",
        "args": ["-lc", "cd /home/eva/.openclaw/workspace/learning-hub-mcp && exec /home/eva/.openclaw/workspace/learning-hub-mcp/.venv/bin/learning-hub-mcp"],
        "cwd": "/home/eva/.openclaw/workspace/learning-hub-mcp",
        "toolPrefix": "learning_hub"
      }
    }
  }
}
```

### Шаг 3: Добавить tools в allowlist агента

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "tools": {
          "allow": [
            "learning-hub"
          ]
        }
      }
    ]
  }
}
```

ID плагина `"learning-hub"` в allowlist включает все tools, зарегистрированные этим плагином.

### Шаг 4: Перезапустить gateway

```bash
openclaw gateway restart
```

### Шаг 5: Проверить

Агент должен видеть `learning_hub_*` инструменты в tool list. Тест:

```
# В вебчате или Telegram спросить агента:
"Покажи домашку CZ"

# Агент должен вызвать learning_hub_list_homeworks напрямую
# (не exec + mcporter)
```

### Шаг 6: Убрать костыль из USER.md

После подтверждения работоспособности убрать из `USER.md` инструкции про mcporter:

```
Удалить:
"В этом деплое Learning Hub MCP не доступен как прямые инструменты вида learning-hub.*"
"Вызывать надо через exec и npx --yes mcporter call …"
```

Агент будет видеть инструменты нативно и не будет нуждаться в текстовых инструкциях.

---

## Промпт для Claude Code

Когда откроешь проект learning-hub-mcp на другом компьютере, дай Claude Code такой промпт:

> Мне нужно создать OpenClaw bridge-плагин, который сделает инструменты этого MCP-сервера доступными как нативные agent tools в OpenClaw.
>
> Прочитай спецификацию в файле `learning-hub-openclaw-plugin-spec.md` в этом репо. Там описано:
> - Почему это нужно (текущий костыль через exec+mcporter сломан)
> - Архитектура (TypeScript-плагин, который запускает этот Python MCP-сервер по STDIO)
> - Структура плагина (openclaw.plugin.json + index.ts)
> - Как регистрировать tools через api.registerTool()
> - Как проксировать вызовы через @modelcontextprotocol/sdk
>
> Создай директорию `learning-hub-bridge/` в этом репо с кодом плагина. Плагин должен:
> 1. Запускать Python MCP-сервер через StdioClientTransport
> 2. Обнаруживать все tools через client.listTools()
> 3. Регистрировать каждый как OpenClaw agent tool с префиксом `learning_hub_`
> 4. Проксировать execute() вызовы в MCP-сервер
> 5. Собирать множественные TextContent блоки в один JSON-массив (обход известной проблемы сериализации FastMCP)
> 6. Обрабатывать переподключение при падении Python-процесса
>
> Держи минимально — цель ~100-150 строк TypeScript, не фреймворк.

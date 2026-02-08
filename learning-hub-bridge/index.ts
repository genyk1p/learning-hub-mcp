// Learning Hub Bridge Plugin for OpenClaw
// Connects to the Python MCP server via STDIO and registers all its tools
// as native OpenClaw agent tools.

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

// ---- Types for OpenClaw plugin API ----
// OpenClaw does not publish type definitions, so we declare the shape we use.

interface ToolRegistration {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  optional?: boolean;
  execute: (id: string, params: Record<string, unknown>) => Promise<ToolResult>;
}

interface ContentBlock {
  type: string;
  text: string;
}

interface ToolResult {
  content: ContentBlock[];
}

interface PluginApi {
  config: Record<string, unknown>;
  registerTool: (tool: ToolRegistration) => void;
  onShutdown?: (callback: () => void) => void;
}

// ---- Default tool prefix ----

const DEFAULT_TOOL_PREFIX = "learning_hub";

// ---- Helper: merge multiple text blocks into one JSON array ----
// FastMCP serializes list[Model] as separate TextContent blocks (one per item).
// This caused a bug in mcporter. We merge them back into a single JSON array.

function mergeTextBlocks(blocks: ContentBlock[]): ContentBlock[] {
  const textBlocks = blocks.filter((b) => b.type === "text");

  // Nothing to merge if 0 or 1 text blocks
  if (textBlocks.length <= 1) {
    return blocks;
  }

  // Try to parse each text block as JSON and combine into an array
  try {
    const parsed = textBlocks.map((b) => JSON.parse(b.text));
    return [{ type: "text", text: JSON.stringify(parsed, null, 2) }];
  } catch {
    // If any block is not valid JSON, return as-is
    return blocks;
  }
}

// ---- Main plugin function ----

export default function learningHubBridge(api: PluginApi) {
  // Read config (command and args are required in openclaw.json)
  // OpenClaw passes the full openclaw.json as api.config.
  // Our plugin config is at plugins.entries["learning-hub"].config
  const fullConfig = api.config ?? {};
  const plugins = (fullConfig.plugins as Record<string, unknown>) ?? {};
  const entries = (plugins.entries as Record<string, unknown>) ?? {};
  const pluginEntry = (entries["learning-hub"] as Record<string, unknown>) ?? {};
  const config: Record<string, unknown> =
    (pluginEntry.config as Record<string, unknown>) ?? {};

  if (!config.command || !config.args) {
    console.error(
      "[learning-hub-bridge] 'command' and 'args' are required in plugin config"
    );
    return;
  }

  const command: string = config.command as string;
  const args: string[] = config.args as string[];
  const cwd: string | undefined = (config.cwd as string) ?? undefined;
  const toolPrefix = (config.toolPrefix as string) ?? DEFAULT_TOOL_PREFIX;

  // MCP client instance (shared across all tool calls)
  let client: Client | null = null;
  let connected = false;

  // Connect to the Python MCP server
  async function ensureConnected(): Promise<Client> {
    if (client !== null && connected) {
      return client;
    }

    const transport = new StdioClientTransport({
      command,
      args,
      ...(cwd ? { cwd } : {}),
    });
    client = new Client({ name: "learning-hub-bridge", version: "1.0.0" });

    await client.connect(transport);
    connected = true;

    // Mark as disconnected when process exits
    transport.onclose = () => {
      connected = false;
    };

    return client;
  }

  // Discover tools and register them in OpenClaw
  async function discoverAndRegister() {
    const mcpClient = await ensureConnected();
    const { tools } = await mcpClient.listTools();

    for (const tool of tools) {
      const toolName = `${toolPrefix}_${tool.name}`;

      api.registerTool({
        name: toolName,
        description: tool.description ?? `Learning Hub: ${tool.name}`,
        parameters: (tool.inputSchema as Record<string, unknown>) ?? {
          type: "object",
          properties: {},
        },
        optional: true,

        async execute(_id: string, params: Record<string, unknown>) {
          // Reconnect if the Python process died
          const c = await ensureConnected();

          const result = await c.callTool({
            name: tool.name,
            arguments: params,
          });

          const blocks = (result.content ?? []) as ContentBlock[];
          return { content: mergeTextBlocks(blocks) };
        },
      });
    }
  }

  // Start discovery (runs in background, does not block gateway startup)
  discoverAndRegister().catch((err) => {
    console.error("[learning-hub-bridge] Failed to start:", err);
  });

  // Clean up when gateway shuts down
  if (api.onShutdown) {
    api.onShutdown(() => {
      if (client !== null) {
        client.close();
        client = null;
        connected = false;
      }
    });
  }
}

"""Tests that tool_names.py stays in sync with actually registered MCP tools."""

import learning_hub.tools.tool_names as tool_names_module
from learning_hub.server import mcp


def _get_registered_tool_names() -> set[str]:
    """Get all tool names registered in the MCP server."""
    return set(mcp._tool_manager._tools.keys())


def _get_registry_tool_names() -> set[str]:
    """Get all tool name values from tool_names.py (TOOL_* constants)."""
    return {
        v
        for k, v in vars(tool_names_module).items()
        if k.startswith("TOOL_") and isinstance(v, str)
    }


def test_no_missing_tools_in_registry():
    """Every MCP tool must have a constant in tool_names.py."""
    registered = _get_registered_tool_names()
    registry = _get_registry_tool_names()
    missing = registered - registry
    assert not missing, (
        f"Tools registered in MCP but missing from tool_names.py: {sorted(missing)}"
    )


def test_no_stale_tools_in_registry():
    """Every constant in tool_names.py must correspond to an actual MCP tool."""
    registered = _get_registered_tool_names()
    registry = _get_registry_tool_names()
    stale = registry - registered
    assert not stale, (
        f"Constants in tool_names.py with no matching MCP tool: {sorted(stale)}"
    )


def test_constant_values_match_names():
    """TOOL_* constant values must match the actual registered tool function names."""
    registered = _get_registered_tool_names()
    for const_name, tool_name in vars(tool_names_module).items():
        if not const_name.startswith("TOOL_") or not isinstance(tool_name, str):
            continue
        assert tool_name in registered, (
            f"{const_name} = \"{tool_name}\" — no such tool registered in MCP"
        )

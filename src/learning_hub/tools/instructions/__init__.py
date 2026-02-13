"""Instruction tools for MCP server.

Returns workflow instructions that the agent should follow
when performing various operations.
"""

from mcp.server.fastmcp import FastMCP

from learning_hub.tools.instructions.book_lookup import BOOK_LOOKUP_INSTRUCTIONS
from learning_hub.tools.instructions.books_workflow import BOOKS_WORKFLOW_INSTRUCTIONS
from learning_hub.tools.instructions.homework_manual import HOMEWORK_MANUAL_INSTRUCTIONS


def register_instruction_tools(mcp: FastMCP) -> None:
    """Register instruction tools that return workflow guides for the agent."""

    @mcp.tool(description="""\
      Get step-by-step instructions for finding and delivering educational materials (textbooks).

      Call this tool when a user asks for a textbook, specific pages, lesson materials,
      or anything related to looking up educational content from the book library.

      Returns a detailed algorithm the agent should follow to search, identify,
      extract, and deliver the right book or pages to the user.""")
    async def get_book_lookup_instructions() -> str:
        return BOOK_LOOKUP_INSTRUCTIONS

    @mcp.tool(description="""\
      Get step-by-step instructions for processing and registering new books into Learning Hub.

      Call this tool when new book files need to be added to the system — typically from
      the temp_book/ folder on the server. Covers the full workflow: creating storage folders,
      generating book.md summaries, linking to subjects, and registering via add_book.

      Returns a detailed algorithm the agent should follow to process and register books.""")
    async def get_books_workflow_instructions() -> str:
        return BOOKS_WORKFLOW_INSTRUCTIONS

    @mcp.tool(description="""\
      Get step-by-step instructions for manually adding homework assignments.

      Call this tool when a parent or other authorized person (NOT the child)
      wants to add a homework assignment manually — not via EduPage sync.

      Returns a detailed algorithm the agent should follow to gather info,
      verify textbook references, confirm with the user, and register the homework.""")
    async def get_homework_manual_instructions() -> str:
        return HOMEWORK_MANUAL_INSTRUCTIONS

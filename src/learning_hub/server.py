"""Learning Hub MCP Server."""

from mcp.server.fastmcp import FastMCP

from learning_hub.tools.subjects import register_subject_tools
from learning_hub.tools.subject_topics import register_subject_topic_tools
from learning_hub.tools.grades import register_grade_tools
from learning_hub.tools.bonus_tasks import register_bonus_task_tools
from learning_hub.tools.homeworks import register_homework_tools
from learning_hub.tools.weeks import register_week_tools
from learning_hub.tools.edupage import register_edupage_tools
from learning_hub.tools.books import register_book_tools
from learning_hub.tools.bonuses import register_bonus_tools
from learning_hub.tools.bonus_funds import register_bonus_fund_tools
from learning_hub.tools.topic_reviews import register_topic_review_tools
from learning_hub.tools.escalation import register_escalation_tools
from learning_hub.tools.family_members import register_family_member_tools
from learning_hub.tools.gateways import register_gateway_tools
from learning_hub.tools.configs import register_config_tools
from learning_hub.tools.instructions import register_instruction_tools

# Create MCP server
mcp = FastMCP("learning-hub")

# Register all tools
register_subject_tools(mcp)
register_subject_topic_tools(mcp)
register_grade_tools(mcp)
register_bonus_task_tools(mcp)
register_homework_tools(mcp)
register_week_tools(mcp)
register_edupage_tools(mcp)
register_book_tools(mcp)
register_bonus_tools(mcp)
register_bonus_fund_tools(mcp)
register_topic_review_tools(mcp)
register_escalation_tools(mcp)
register_family_member_tools(mcp)
register_gateway_tools(mcp)
register_config_tools(mcp)
register_instruction_tools(mcp)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()

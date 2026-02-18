"""Instruction tools for MCP server.

Returns workflow instructions that the agent should follow
when performing various operations.
"""

from mcp.server.fastmcp import FastMCP

from learning_hub.tools.tool_names import (
    TOOL_GET_BOOK_LOOKUP_INSTRUCTIONS,
    TOOL_GET_BOOKS_WORKFLOW_INSTRUCTIONS,
    TOOL_GET_GRADE_MANUAL_INSTRUCTIONS,
    TOOL_GET_HOMEWORK_MANUAL_INSTRUCTIONS,
    TOOL_GET_STUDENT_REQUEST_ROUTER_INSTRUCTIONS,
    TOOL_GET_BONUS_TASK_ASSIGNMENT_INSTRUCTIONS,
    TOOL_GET_SUBMISSION_ROUTING_INSTRUCTIONS,
    TOOL_GET_BONUS_TASK_EVALUATION_INSTRUCTIONS,
    TOOL_GET_HOMEWORK_EVALUATION_INSTRUCTIONS,
    TOOL_GET_TOPIC_REVIEW_CURATION_INSTRUCTIONS,
)
from learning_hub.tools.instructions.book_lookup import BOOK_LOOKUP_INSTRUCTIONS
from learning_hub.tools.instructions.books_workflow import BOOKS_WORKFLOW_INSTRUCTIONS
from learning_hub.tools.instructions.homework_manual import HOMEWORK_MANUAL_INSTRUCTIONS
from learning_hub.tools.instructions.student_request_router import (
    STUDENT_REQUEST_ROUTER_INSTRUCTIONS,
)
from learning_hub.tools.instructions.bonus_task_assignment import (
    BONUS_TASK_ASSIGNMENT_INSTRUCTIONS,
)
from learning_hub.tools.instructions.submission_routing import (
    SUBMISSION_ROUTING_INSTRUCTIONS,
)
from learning_hub.tools.instructions.bonus_task_evaluation import (
    BONUS_TASK_EVALUATION_INSTRUCTIONS,
)
from learning_hub.tools.instructions.homework_evaluation import (
    HOMEWORK_EVALUATION_INSTRUCTIONS,
)
from learning_hub.tools.instructions.grade_manual import GRADE_MANUAL_INSTRUCTIONS
from learning_hub.tools.instructions.topic_review_curation import (
    TOPIC_REVIEW_CURATION_INSTRUCTIONS,
)


def register_instruction_tools(mcp: FastMCP) -> None:
    """Register instruction tools that return workflow guides for the agent."""

    @mcp.tool(name=TOOL_GET_GRADE_MANUAL_INSTRUCTIONS, description="""\
      Get step-by-step instructions for manually adding a grade.

      Call this tool when a parent or other authorized person (NOT the child)
      wants to add a grade manually — not via EduPage sync
      and not via bonus task evaluation.

      Returns a detailed algorithm the agent should follow to gather info,
      verify the grading scale, check for duplicates, and record the grade.""")
    async def get_grade_manual_instructions() -> str:
        return GRADE_MANUAL_INSTRUCTIONS

    @mcp.tool(name=TOOL_GET_BOOK_LOOKUP_INSTRUCTIONS, description="""\
      Get step-by-step instructions for finding and delivering educational materials (textbooks).

      Call this tool when a user asks for a textbook, specific pages, lesson materials,
      or anything related to looking up educational content from the book library.

      Returns a detailed algorithm the agent should follow to search, identify,
      extract, and deliver the right book or pages to the user.""")
    async def get_book_lookup_instructions() -> str:
        return BOOK_LOOKUP_INSTRUCTIONS

    @mcp.tool(name=TOOL_GET_BOOKS_WORKFLOW_INSTRUCTIONS, description="""\
      Get step-by-step instructions for processing and registering new books into Learning Hub.

      Call this tool when new book files need to be added to the system — typically from
      the temp_book/ folder on the server. Covers the full workflow: creating storage folders,
      generating book.md summaries, linking to subjects, and registering via add_book.

      Returns a detailed algorithm the agent should follow to process and register books.""")
    async def get_books_workflow_instructions() -> str:
        return BOOKS_WORKFLOW_INSTRUCTIONS

    @mcp.tool(name=TOOL_GET_HOMEWORK_MANUAL_INSTRUCTIONS, description="""\
      Get step-by-step instructions for manually adding homework assignments.

      Call this tool when a parent or other authorized person (NOT the child)
      wants to add a homework assignment manually — not via EduPage sync.

      Returns a detailed algorithm the agent should follow to gather info,
      verify textbook references, confirm with the user, and register the homework.""")
    async def get_homework_manual_instructions() -> str:
        return HOMEWORK_MANUAL_INSTRUCTIONS

    @mcp.tool(name=TOOL_GET_STUDENT_REQUEST_ROUTER_INSTRUCTIONS, description="""\
      Get the entry-point instruction for handling student messages about learning.

      Call this tool FIRST when the student writes anything related to homework,
      grades, bonus tasks, or game minutes. It classifies the request type
      (facts / bonus task request / submission) and tells which instruction tool
      to call next.

      Returns a classification flowchart with scenario descriptions.""")
    async def get_student_request_router_instructions() -> str:
        return STUDENT_REQUEST_ROUTER_INSTRUCTIONS

    @mcp.tool(name=TOOL_GET_BONUS_TASK_ASSIGNMENT_INSTRUCTIONS, description="""\
      Get step-by-step instructions for creating and assigning a bonus task.

      Call this tool when the student asks for a bonus task to earn game minutes.
      Covers: checking the bonus fund, selecting a TopicReview by priority,
      formulating the task, and registering it in Learning Hub.

      Returns a detailed algorithm for bonus task assignment.""")
    async def get_bonus_task_assignment_instructions() -> str:
        return BONUS_TASK_ASSIGNMENT_INSTRUCTIONS

    @mcp.tool(name=TOOL_GET_SUBMISSION_ROUTING_INSTRUCTIONS, description="""\
      Get step-by-step instructions for classifying a student's submission.

      Call this tool when the student sends an answer or completed work,
      and you need to determine whether it is a bonus task or homework
      (and which school). Covers: checking pending tasks, matching by context,
      and asking clarifying questions.

      Returns a classification algorithm with decision tree.""")
    async def get_submission_routing_instructions() -> str:
        return SUBMISSION_ROUTING_INSTRUCTIONS

    @mcp.tool(name=TOOL_GET_BONUS_TASK_EVALUATION_INSTRUCTIONS, description="""\
      Get step-by-step instructions for evaluating a bonus task submission.

      Call this tool after determining that the student is submitting a bonus task.
      Covers: loading the task, evaluating the answer, commit-before-confirm rule,
      applying results, grading, and closing TopicReview.

      Returns a detailed evaluation algorithm.""")
    async def get_bonus_task_evaluation_instructions() -> str:
        return BONUS_TASK_EVALUATION_INSTRUCTIONS

    @mcp.tool(name=TOOL_GET_HOMEWORK_EVALUATION_INSTRUCTIONS, description="""\
      Get step-by-step instructions for evaluating a homework submission.

      Call this tool after determining that the student is submitting homework.
      Covers: finding the homework, loading book context, evaluating the answer,
      handling unverifiable tasks, setting recommended grade, and escalation.
      Works for any school type.

      Returns a detailed evaluation algorithm.""")
    async def get_homework_evaluation_instructions() -> str:
        return HOMEWORK_EVALUATION_INSTRUCTIONS

    @mcp.tool(name=TOOL_GET_TOPIC_REVIEW_CURATION_INSTRUCTIONS, description="""\
      Get step-by-step instructions for curating TopicReviews after EduPage sync.

      Call this tool after running sync_edupage_grades. The sync may create
      TopicReview records for non-academic subjects (PE, crafts, music, art)
      that don't need reinforcement. This instruction tells how to identify
      and close them.

      Returns a curation algorithm with examples of irrelevant subjects.""")
    async def get_topic_review_curation_instructions() -> str:
        return TOPIC_REVIEW_CURATION_INSTRUCTIONS

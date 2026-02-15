"""Central registry of all MCP tool names.

Used by instruction tools to reference other tools safely.
If a tool is renamed here, all instruction texts using the constant
will update automatically via f-strings.
"""

# --- Subjects ---
TOOL_CREATE_SUBJECT = "create_subject"
TOOL_LIST_SUBJECTS = "list_subjects"
TOOL_UPDATE_SUBJECT = "update_subject"

# --- Subject Topics ---
TOOL_CREATE_TOPIC = "create_topic"
TOOL_LIST_TOPICS = "list_topics"
TOOL_CLOSE_TOPIC = "close_topic"

# --- Grades ---
TOOL_ADD_GRADE = "add_grade"
TOOL_LIST_GRADES = "list_grades"
TOOL_UPDATE_GRADE = "update_grade"

# --- Bonus Tasks ---
TOOL_CREATE_BONUS_TASK = "create_bonus_task"
TOOL_LIST_BONUS_TASKS = "list_bonus_tasks"
TOOL_COMPLETE_BONUS_TASK = "complete_bonus_task"
TOOL_GET_BONUS_TASK = "get_bonus_task"
TOOL_GET_LATEST_BONUS_TASK = "get_latest_bonus_task"
TOOL_CANCEL_BONUS_TASK = "cancel_bonus_task"
TOOL_APPLY_BONUS_TASK_RESULT = "apply_bonus_task_result"

# --- Bonuses ---
TOOL_CREATE_BONUS = "create_bonus"
TOOL_DELETE_BONUS = "delete_bonus"
TOOL_LIST_UNREWARDED_BONUSES = "list_unrewarded_bonuses"
TOOL_MARK_BONUSES_REWARDED = "mark_bonuses_rewarded"

# --- Bonus Funds ---
TOOL_GET_BONUS_FUND = "get_bonus_fund"
TOOL_ADD_TASKS_TO_FUND = "add_tasks_to_fund"

# --- Homeworks ---
TOOL_CREATE_HOMEWORK = "create_homework"
TOOL_LIST_HOMEWORKS = "list_homeworks"
TOOL_CLOSE_OVERDUE_HOMEWORKS = "close_overdue_homeworks"
TOOL_COMPLETE_HOMEWORK = "complete_homework"
TOOL_UPDATE_HOMEWORK = "update_homework"

# --- Books ---
TOOL_ADD_BOOK = "add_book"
TOOL_LIST_BOOKS = "list_books"
TOOL_GET_BOOK = "get_book"
TOOL_UPDATE_BOOK = "update_book"
TOOL_DELETE_BOOK = "delete_book"

# --- Weeks ---
TOOL_CREATE_WEEK = "create_week"
TOOL_GET_WEEK = "get_week"
TOOL_UPDATE_WEEK = "update_week"
TOOL_FINALIZE_WEEK = "finalize_week"

# --- Topic Reviews ---
TOOL_LIST_TOPIC_REVIEWS = "list_topic_reviews"
TOOL_MARK_TOPIC_REINFORCED = "mark_topic_reinforced"
TOOL_GET_PENDING_REVIEWS_FOR_TOPIC = "get_pending_reviews_for_topic"
TOOL_INCREMENT_TOPIC_REPEAT_COUNT = "increment_topic_repeat_count"

# --- Escalation ---
TOOL_GET_GRADES_PENDING_ESCALATION = "get_grades_pending_escalation"
TOOL_MARK_GRADES_ESCALATED = "mark_grades_escalated"

# --- EduPage Sync ---
TOOL_SYNC_EDUPAGE_GRADES = "sync_edupage_grades"
TOOL_SYNC_EDUPAGE_HOMEWORKS = "sync_edupage_homeworks"

# --- Instruction Tools ---
TOOL_GET_BOOK_LOOKUP_INSTRUCTIONS = "get_book_lookup_instructions"
TOOL_GET_BOOKS_WORKFLOW_INSTRUCTIONS = "get_books_workflow_instructions"
TOOL_GET_HOMEWORK_MANUAL_INSTRUCTIONS = "get_homework_manual_instructions"
TOOL_GET_STUDENT_REQUEST_ROUTER_INSTRUCTIONS = "get_student_request_router_instructions"
TOOL_GET_BONUS_TASK_ASSIGNMENT_INSTRUCTIONS = "get_bonus_task_assignment_instructions"
TOOL_GET_SUBMISSION_ROUTING_INSTRUCTIONS = "get_submission_routing_instructions"
TOOL_GET_BONUS_TASK_EVALUATION_INSTRUCTIONS = "get_bonus_task_evaluation_instructions"
TOOL_GET_HOMEWORK_EVALUATION_INSTRUCTIONS = "get_homework_evaluation_instructions"
TOOL_GET_TOPIC_REVIEW_CURATION_INSTRUCTIONS = "get_topic_review_curation_instructions"

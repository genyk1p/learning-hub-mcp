"""Central registry of all MCP tool names.

Used by instruction tools to reference other tools safely.
If a tool is renamed here, all instruction texts using the constant
will update automatically via f-strings.
"""

# --- Schools ---
TOOL_CREATE_SCHOOL = "create_school"
TOOL_LIST_SCHOOLS = "list_schools"
TOOL_GET_SCHOOL = "get_school"
TOOL_UPDATE_SCHOOL = "update_school"

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
TOOL_CHECK_PENDING_BONUS_TASK = "check_pending_bonus_task"

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
TOOL_GET_PENDING_HOMEWORK_REMINDERS = "get_pending_homework_reminders"
TOOL_MARK_HOMEWORK_REMINDERS_SENT = "mark_homework_reminders_sent"

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
TOOL_CALCULATE_WEEKLY_MINUTES = "calculate_weekly_minutes"
TOOL_GET_GRADE_TO_MINUTES_MAP = "get_grade_to_minutes_map"

# --- Topic Reviews ---
TOOL_LIST_TOPIC_REVIEWS = "list_topic_reviews"
TOOL_MARK_TOPIC_REINFORCED = "mark_topic_reinforced"
TOOL_GET_PENDING_REVIEWS_FOR_TOPIC = "get_pending_reviews_for_topic"
TOOL_INCREMENT_TOPIC_REPEAT_COUNT = "increment_topic_repeat_count"
TOOL_GET_PRIORITY_TOPIC_FOR_REVIEW = "get_priority_topic_for_review"

# --- Family Members ---
TOOL_CREATE_FAMILY_MEMBER = "create_family_member"
TOOL_LIST_FAMILY_MEMBERS = "list_family_members"
TOOL_UPDATE_FAMILY_MEMBER = "update_family_member"
TOOL_DELETE_FAMILY_MEMBER = "delete_family_member"
TOOL_GET_STUDENT = "get_student"

# --- Gateways ---
TOOL_CREATE_GATEWAY = "create_gateway"
TOOL_LIST_GATEWAYS = "list_gateways"
TOOL_UPDATE_GATEWAY = "update_gateway"
TOOL_DELETE_GATEWAY = "delete_gateway"
TOOL_LOOKUP_GATEWAY = "lookup_gateway"

# --- Configs ---
TOOL_GET_CONFIG = "get_config"
TOOL_SET_CONFIG = "set_config"
TOOL_LIST_CONFIGS = "list_configs"
TOOL_LIST_REQUIRED_UNSET_CONFIGS = "list_required_unset_configs"

# --- Escalation ---
TOOL_GET_GRADES_PENDING_ESCALATION = "get_grades_pending_escalation"
TOOL_MARK_GRADES_ESCALATED = "mark_grades_escalated"

# --- EduPage Sync ---
TOOL_SYNC_EDUPAGE_GRADES = "sync_edupage_grades"
TOOL_SYNC_EDUPAGE_HOMEWORKS = "sync_edupage_homeworks"

# --- Instruction Tools ---
TOOL_GET_GRADE_MANUAL_INSTRUCTIONS = "get_grade_manual_instructions"
TOOL_GET_BOOK_LOOKUP_INSTRUCTIONS = "get_book_lookup_instructions"
TOOL_GET_BOOKS_WORKFLOW_INSTRUCTIONS = "get_books_workflow_instructions"
TOOL_GET_HOMEWORK_MANUAL_INSTRUCTIONS = "get_homework_manual_instructions"
TOOL_GET_STUDENT_REQUEST_ROUTER_INSTRUCTIONS = "get_student_request_router_instructions"
TOOL_GET_BONUS_TASK_ASSIGNMENT_INSTRUCTIONS = "get_bonus_task_assignment_instructions"
TOOL_GET_SUBMISSION_ROUTING_INSTRUCTIONS = "get_submission_routing_instructions"
TOOL_GET_BONUS_TASK_EVALUATION_INSTRUCTIONS = "get_bonus_task_evaluation_instructions"
TOOL_GET_HOMEWORK_EVALUATION_INSTRUCTIONS = "get_homework_evaluation_instructions"
TOOL_GET_TOPIC_REVIEW_CURATION_INSTRUCTIONS = "get_topic_review_curation_instructions"

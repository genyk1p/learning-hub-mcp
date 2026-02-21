"""Config key constants referenced in tool descriptions and instruction f-strings.

If a key is renamed, all tool descriptions and instruction texts update automatically.
"""

# Path to the issue log file for logging problems
CFG_ISSUES_LOG = "ISSUES_LOG"

# Folder where users place book files for processing
CFG_TEMP_BOOK_DIR = "TEMP_BOOK_DIR"

# Base folder for storing processed books
CFG_BOOKS_STORAGE_DIR = "BOOKS_STORAGE_DIR"

# Required repetitions per grade before TopicReview is closed (JSON map)
CFG_TOPIC_REVIEW_THRESHOLDS = "TOPIC_REVIEW_THRESHOLDS"

# Language for communication with the family
CFG_FAMILY_LANGUAGE = "FAMILY_LANGUAGE"

# Grade to game minutes conversion (JSON map)
CFG_GRADE_MINUTES_MAP = "GRADE_MINUTES_MAP"

# Bonus minutes for on-time homework
CFG_HOMEWORK_BONUS_MINUTES_ONTIME = "HOMEWORK_BONUS_MINUTES_ONTIME"

# Penalty minutes for overdue homework
CFG_HOMEWORK_BONUS_MINUTES_OVERDUE = "HOMEWORK_BONUS_MINUTES_OVERDUE"

# Bonus task slots added each week
CFG_BONUS_FUND_WEEKLY_TOPUP = "BONUS_FUND_WEEKLY_TOPUP"

# Default time for deadline when only date is specified (HH:MM)
CFG_DEFAULT_DEADLINE_TIME = "DEFAULT_DEADLINE_TIME"

# Whether initial setup has been completed (true/false)
CFG_SETUP_COMPLETED = "SETUP_COMPLETED"

"""Central registry of config variable names referenced in instruction tools.

These variables are defined by the agent platform (e.g. in USER.md).
Instructions reference them by name, the agent resolves them
to actual values from its config.

If a variable is renamed here, all instruction texts using the constant
will update automatically via f-strings.
"""

# Path to the issue log file for logging problems
CFG_ISSUES_LOG = "ISSUES_LOG"

# Path to JSON mapping subject → responsible adult
CFG_SUBJECT_RESPONSIBLES = "SUBJECT_RESPONSIBLES"

# Folder where users place book files for processing
CFG_TEMP_BOOK_DIR = "TEMP_BOOK_DIR"

# Base folder for storing processed books
CFG_BOOKS_STORAGE_DIR = "BOOKS_STORAGE_DIR"

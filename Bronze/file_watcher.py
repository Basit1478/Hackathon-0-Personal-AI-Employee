"""
Bronze Tier AI Employee - File Watcher (Production Ready)
==========================================================
This script monitors the Inbox folder for new files and automatically
creates task files in the Needs_Action folder.

Technical Approach:
- Checks the Inbox folder every 5 seconds
- Tracks which files have been processed to avoid duplicates
- Creates structured task files in Markdown format
- Includes comprehensive error handling and logging
- Gracefully recovers from errors without crashing

Error Handling:
- All critical operations are wrapped in try-catch blocks
- Errors are logged to watcher_errors.log
- If something fails, it's logged and the script continues
- To read errors: check watcher_errors.log in the same folder
- To restart after crash: simply run 'python file_watcher.py' again
"""

import os
import sys
import time
import logging
from datetime import datetime


# ============================================================================
# CONFIGURATION
# ============================================================================

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define folder paths relative to script location
INBOX_FOLDER = os.path.join(SCRIPT_DIR, "Inbox")
NEEDS_ACTION_FOLDER = os.path.join(SCRIPT_DIR, "Needs_Action")
LOG_FILE = os.path.join(SCRIPT_DIR, "watcher_errors.log")

# How often to check for new files (in seconds)
CHECK_INTERVAL = 5

# Track files we've already processed (to avoid duplicates)
# This is a set that stores filenames we've seen
processed_files = set()

# Global logger instance
logger = None


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging():
    """
    Configures the logging system to write errors to watcher_errors.log.

    This creates a log file that captures:
    - Error messages when something goes wrong
    - Warnings for non-critical issues
    - Timestamps for when errors occurred

    How to read the log:
    1. Open watcher_errors.log in a text editor
    2. Each line shows: [timestamp] LEVEL: message
    3. ERROR = something went wrong
    4. WARNING = potential issue but not critical
    5. INFO = general status information
    """
    global logger

    try:
        # Create logger instance
        logger = logging.getLogger('FileWatcher')
        logger.setLevel(logging.INFO)

        # Create file handler for logging to file
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # Create console handler for displaying errors on screen
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)

        # Create formatter for log messages
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        logger.info("=" * 70)
        logger.info("File Watcher logging initialized")
        logger.info(f"Log file: {LOG_FILE}")
        logger.info("=" * 70)

        return True

    except Exception as e:
        print(f"⚠️  Failed to setup logging: {e}")
        print("⚠️  Continuing without file logging...")
        return False


# ============================================================================
# FOLDER MANAGEMENT
# ============================================================================

def ensure_folders_exist():
    """
    Startup check: Verifies that required folders exist.
    If they don't exist, creates them automatically.

    This prevents the script from crashing if folders are missing.

    Returns:
        bool: True if folders exist or were created, False if creation failed
    """
    folders_to_check = [
        ("Inbox", INBOX_FOLDER),
        ("Needs_Action", NEEDS_ACTION_FOLDER)
    ]

    all_ok = True

    for folder_name, folder_path in folders_to_check:
        try:
            if not os.path.exists(folder_path):
                # Folder doesn't exist - create it
                os.makedirs(folder_path)
                print(f"✅ Created missing folder: {folder_name}/")
                if logger:
                    logger.info(f"Created missing folder: {folder_path}")
            else:
                # Folder exists - verify it's actually a directory
                if not os.path.isdir(folder_path):
                    print(f"❌ Error: {folder_name} exists but is not a folder!")
                    if logger:
                        logger.error(f"{folder_path} exists but is not a directory")
                    all_ok = False

        except Exception as e:
            print(f"❌ Error checking/creating {folder_name} folder: {e}")
            if logger:
                logger.error(f"Failed to create folder {folder_path}: {e}")
            all_ok = False

    return all_ok


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_timestamp():
    """
    Returns the current date and time as a formatted string.
    Format: YYYY-MM-DD HH:MM:SS
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_human_readable_size(size_bytes):
    """
    Converts bytes to human-readable file size format.

    Args:
        size_bytes (int): File size in bytes

    Returns:
        str: Human-readable size (e.g., "1.5 KB", "2.3 MB")
    """
    try:
        # Define size units
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    except Exception as e:
        if logger:
            logger.warning(f"Error converting file size: {e}")
        return "Unknown"


def get_files_in_inbox():
    """
    Gets a list of all files currently in the Inbox folder.

    Error Handling:
    - If Inbox folder doesn't exist, returns empty list and logs error
    - If permission denied, returns empty list and logs error
    - If any other error, returns empty list and logs error

    Returns:
        list: A list of filenames (not full paths), or empty list on error
    """
    try:
        # os.listdir() returns all items in a folder
        all_items = os.listdir(INBOX_FOLDER)

        # Filter to only include files (not folders)
        files = []
        for item in all_items:
            try:
                full_path = os.path.join(INBOX_FOLDER, item)
                # os.path.isfile() checks if something is a file
                if os.path.isfile(full_path):
                    files.append(item)
            except Exception as e:
                # If we can't check a specific item, log and skip it
                if logger:
                    logger.warning(f"Could not check item '{item}': {e}")
                continue

        return files

    except FileNotFoundError:
        error_msg = f"Inbox folder not found at {INBOX_FOLDER}"
        print(f"⚠️  Error: {error_msg}")
        if logger:
            logger.error(error_msg)
        return []

    except PermissionError:
        error_msg = f"Permission denied accessing Inbox folder: {INBOX_FOLDER}"
        print(f"⚠️  Error: {error_msg}")
        if logger:
            logger.error(error_msg)
        return []

    except Exception as e:
        error_msg = f"Error reading Inbox folder: {e}"
        print(f"⚠️  Error: {error_msg}")
        if logger:
            logger.error(error_msg)
        return []


def create_task_file(filename):
    """
    Creates a task file in the Needs_Action folder for a new inbox file.

    Error Handling:
    - If task file already exists, skips creation
    - If can't get file size, uses "Unknown"
    - If can't write task file, logs error and continues
    - All errors are caught and logged without crashing

    Args:
        filename (str): The name of the file found in Inbox

    Returns:
        bool: True if task was created successfully, False otherwise
    """
    try:
        # Create a safe task filename based on the original filename
        # Replace spaces and special characters with underscores
        safe_name = filename.replace(" ", "_").replace(".", "_")
        task_filename = f"task_{safe_name}.md"

        # Full path where we'll save the task file
        task_path = os.path.join(NEEDS_ACTION_FOLDER, task_filename)

        # Check if this task file already exists (extra safety check)
        if os.path.exists(task_path):
            print(f"⚠️  Task already exists for {filename}, skipping...")
            if logger:
                logger.warning(f"Task already exists: {task_filename}")
            return False

        # Get current timestamp
        timestamp = get_current_timestamp()

        # Get file size information
        # WRAPPED IN TRY-CATCH: If we can't get size, use defaults
        source_file_path = os.path.join(INBOX_FOLDER, filename)
        try:
            file_size_bytes = os.path.getsize(source_file_path)
            file_size_human = get_human_readable_size(file_size_bytes)
        except FileNotFoundError:
            # File disappeared between detection and now
            if logger:
                logger.warning(f"File disappeared before task creation: {filename}")
            file_size_bytes = 0
            file_size_human = "Unknown (file not found)"
        except Exception as e:
            if logger:
                logger.warning(f"Could not get file size for {filename}: {e}")
            file_size_bytes = 0
            file_size_human = "Unknown"

        # Create the enhanced task file content with professional format
        task_content = f"""---
type: file_review
status: pending
priority: normal
source: Inbox
filename: {filename}
file_size: {file_size_bytes}
created_at: {timestamp}
tags: []
---

# Task: Review File - {filename}

## File Information
- **Source**: Inbox
- **Size**: {file_size_human}
- **Detected**: {timestamp}

## Required Actions
- [ ] Review the file content
- [ ] Decide what action is needed
- [ ] Tag appropriately (urgent/invoice/client/personal)
- [ ] Move to Done when complete

## Notes
(Add your observations here)
"""

        # Write the task file
        # WRAPPED IN TRY-CATCH: If write fails, log and return False
        try:
            with open(task_path, 'w', encoding='utf-8') as f:
                f.write(task_content)

            print(f"✅ Created task: {task_filename}")
            print(f"   Source file: {filename}")
            print(f"   Size: {file_size_human}")
            print(f"   Time: {timestamp}")

            if logger:
                logger.info(f"Created task: {task_filename} for {filename} ({file_size_human})")

            return True

        except PermissionError:
            error_msg = f"Permission denied writing task file: {task_filename}"
            print(f"⚠️  Error: {error_msg}")
            if logger:
                logger.error(error_msg)
            return False

        except Exception as e:
            error_msg = f"Error creating task file {task_filename}: {e}"
            print(f"⚠️  Error: {error_msg}")
            if logger:
                logger.error(error_msg)
            return False

    except Exception as e:
        # Catch-all for any unexpected errors in the entire function
        error_msg = f"Unexpected error in create_task_file for {filename}: {e}"
        print(f"⚠️  Error: {error_msg}")
        if logger:
            logger.error(error_msg)
        return False


def check_for_new_files():
    """
    Checks the Inbox folder for new files and creates tasks for them.
    This is the main logic that runs every 5 seconds.

    Error Handling:
    - If getting file list fails, returns without crashing
    - If creating a task fails, logs error and continues with next file
    - All errors are caught and logged without stopping the watcher
    """
    try:
        # Get current list of files in Inbox
        current_files = get_files_in_inbox()

        # Check each file to see if it's new
        for filename in current_files:
            try:
                # Skip hidden files (start with .)
                if filename.startswith('.'):
                    continue

                # Check if we've already processed this file
                if filename not in processed_files:
                    # This is a new file!
                    print(f"\n📥 New file detected: {filename}")
                    if logger:
                        logger.info(f"New file detected: {filename}")

                    # Create a task for it
                    # WRAPPED IN TRY-CATCH: If task creation fails, log and continue
                    success = create_task_file(filename)

                    if success:
                        # Mark it as processed so we don't create duplicate tasks
                        processed_files.add(filename)
                    else:
                        # Task creation failed, but we still mark as processed
                        # to avoid repeated attempts
                        processed_files.add(filename)
                        if logger:
                            logger.warning(f"Marked {filename} as processed despite task creation failure")

            except Exception as e:
                # If processing a single file fails, log and continue with next
                error_msg = f"Error processing file {filename}: {e}"
                print(f"⚠️  {error_msg}")
                if logger:
                    logger.error(error_msg)
                continue

    except Exception as e:
        # If the entire check fails, log and return
        error_msg = f"Error in check_for_new_files: {e}"
        print(f"⚠️  {error_msg}")
        if logger:
            logger.error(error_msg)


# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    """
    Main function that runs the file watcher continuously.

    Error Handling Strategy:
    1. Setup logging first (if it fails, continue without it)
    2. Check/create required folders (if fails, exit gracefully)
    3. Perform initial scan (if fails, log and continue with empty set)
    4. Enter main loop with error recovery (catches all errors, never crashes)
    5. Handle Ctrl+C gracefully for clean shutdown

    Recovery from Crashes:
    - If the script crashes, simply run 'python file_watcher.py' again
    - All processed files are tracked in memory (lost on restart)
    - On restart, existing Inbox files are marked as "already processed"
    - This prevents duplicate task creation after restart
    """
    print("=" * 70)
    print("🤖 Bronze Tier AI Employee - File Watcher (Production Ready)")
    print("=" * 70)
    print(f"📂 Monitoring: {INBOX_FOLDER}")
    print(f"📋 Creating tasks in: {NEEDS_ACTION_FOLDER}")
    print(f"⏱️  Check interval: {CHECK_INTERVAL} seconds")
    print(f"📝 Error log: {LOG_FILE}")
    print("=" * 70)
    print("\n⌨️  Press Ctrl+C to stop the watcher\n")

    # STEP 1: Setup logging
    # If this fails, we continue without file logging
    setup_logging()

    # STEP 2: Startup check - ensure required folders exist
    # If this fails, we exit because we can't function without folders
    print("🔍 Checking required folders...")
    if not ensure_folders_exist():
        print("\n❌ Failed to create required folders. Exiting.")
        if logger:
            logger.error("Failed to create required folders. Exiting.")
        return
    print("✅ All required folders present\n")

    # STEP 3: Initial scan to mark existing files as already processed
    # WRAPPED IN TRY-CATCH: If scan fails, we continue with empty processed set
    try:
        print("🔍 Performing initial scan...")
        initial_files = get_files_in_inbox()
        for filename in initial_files:
            if not filename.startswith('.'):
                processed_files.add(filename)
        print(f"📊 Found {len(processed_files)} existing file(s) in Inbox")
        if logger:
            logger.info(f"Initial scan complete: {len(processed_files)} existing files")
        print("✅ Initial scan complete. Now watching for new files...\n")
    except Exception as e:
        error_msg = f"Error during initial scan: {e}"
        print(f"⚠️  {error_msg}")
        if logger:
            logger.error(error_msg)
        print("⚠️  Continuing with empty processed file list...\n")

    # STEP 4: Main monitoring loop with comprehensive error handling
    error_count = 0
    max_consecutive_errors = 10

    try:
        while True:
            try:
                # Check for new files
                # WRAPPED IN TRY-CATCH: If check fails, log and retry after sleep
                check_for_new_files()

                # Reset error count on successful check
                error_count = 0

                # Wait before checking again
                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                # User pressed Ctrl+C - re-raise to outer handler
                raise

            except Exception as e:
                # Something went wrong in the main loop
                # Log it and continue (graceful recovery)
                error_count += 1
                error_msg = f"Error in main loop (count: {error_count}): {e}"
                print(f"\n⚠️  {error_msg}")
                if logger:
                    logger.error(error_msg)

                # If too many consecutive errors, something is seriously wrong
                if error_count >= max_consecutive_errors:
                    print(f"\n❌ Too many consecutive errors ({error_count}). Stopping.")
                    if logger:
                        logger.critical(f"Stopping due to {error_count} consecutive errors")
                    break

                # Wait a bit before retrying
                print(f"⏳ Waiting {CHECK_INTERVAL} seconds before retry...")
                time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        # User pressed Ctrl+C to stop - clean shutdown
        print("\n\n" + "=" * 70)
        print("🛑 File watcher stopped by user")
        print(f"📊 Total files processed: {len(processed_files)}")
        if logger:
            logger.info(f"File watcher stopped by user. Files processed: {len(processed_files)}")
        print("=" * 70)

    except Exception as e:
        # Unexpected fatal error - log and exit
        print("\n\n" + "=" * 70)
        print(f"❌ Fatal error: {e}")
        if logger:
            logger.critical(f"Fatal error caused shutdown: {e}")
        print(f"📝 Check {LOG_FILE} for details")
        print("🔄 Restart by running: python file_watcher.py")
        print("=" * 70)


# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

# This block only runs if the script is executed directly
# (not if it's imported as a module)
if __name__ == "__main__":
    main()

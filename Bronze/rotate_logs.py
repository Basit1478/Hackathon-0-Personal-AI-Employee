"""
Bronze Tier AI Employee - Log Rotation System
==============================================
This script rotates old entries from System_Log.md to dated archive files
in the Logs/ folder to keep the main log clean and manageable.

Purpose:
- Keeps System_Log.md focused on recent activity (today's entries)
- Archives older entries to Logs/YYYY-MM-DD.md files
- Maintains a clean, organized logging system
- Can be run manually or scheduled daily

Usage:
    python rotate_logs.py

What it does:
1. Reads System_Log.md
2. Identifies entries older than today
3. Moves them to dated archive files in Logs/
4. Updates System_Log.md with only today's entries
5. Updates rotation status metadata
"""

import os
import re
from datetime import datetime, timedelta
from collections import defaultdict


# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_LOG_PATH = os.path.join(SCRIPT_DIR, "System_Log.md")
LOGS_FOLDER = os.path.join(SCRIPT_DIR, "Logs")
BACKUP_FOLDER = os.path.join(LOGS_FOLDER, "backups")

# Ensure Logs folder exists
os.makedirs(LOGS_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_today_date():
    """Returns today's date as YYYY-MM-DD string."""
    return datetime.now().strftime("%Y-%m-%d")


def parse_date_from_header(header_line):
    """
    Extracts date from a markdown header like '### 2026-02-12'.

    Args:
        header_line (str): Line containing date header

    Returns:
        str: Date in YYYY-MM-DD format, or None if not found
    """
    match = re.search(r'(\d{4}-\d{2}-\d{2})', header_line)
    if match:
        return match.group(1)
    return None


def create_backup():
    """
    Creates a backup of System_Log.md before rotation.

    Returns:
        str: Path to backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_FOLDER, f"System_Log_backup_{timestamp}.md")

    try:
        with open(SYSTEM_LOG_PATH, 'r', encoding='utf-8') as source:
            content = source.read()

        with open(backup_path, 'w', encoding='utf-8') as backup:
            backup.write(content)

        print(f"✅ Backup created: {backup_path}")
        return backup_path

    except Exception as e:
        print(f"⚠️  Warning: Could not create backup: {e}")
        return None


def read_system_log():
    """
    Reads and parses System_Log.md.

    Returns:
        tuple: (header_lines, entries_by_date, footer_lines)
            - header_lines: Lines before Activity Log section
            - entries_by_date: Dict mapping dates to their log entries
            - footer_lines: Lines after Activity Log section (template, notes)
    """
    try:
        with open(SYSTEM_LOG_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ Error: System_Log.md not found at {SYSTEM_LOG_PATH}")
        return None, None, None
    except Exception as e:
        print(f"❌ Error reading System_Log.md: {e}")
        return None, None, None

    header_lines = []
    entries_by_date = defaultdict(list)
    footer_lines = []

    current_section = 'header'
    current_date = None
    current_entry = []

    for line in lines:
        # Check if we've reached the Activity Log section
        if '## Activity Log' in line:
            current_section = 'activity'
            continue

        # Check if we've reached the footer (template or notes)
        if current_section == 'activity' and ('## Log Entry Template' in line or '## Notes' in line):
            # Save any pending entry
            if current_date and current_entry:
                entries_by_date[current_date].extend(current_entry)
            current_section = 'footer'
            footer_lines.append(line)
            continue

        # Process based on current section
        if current_section == 'header':
            header_lines.append(line)

        elif current_section == 'activity':
            # Check for date header (### YYYY-MM-DD)
            if line.startswith('###'):
                # Save previous entry if exists
                if current_date and current_entry:
                    entries_by_date[current_date].extend(current_entry)

                # Start new date section
                current_date = parse_date_from_header(line)
                current_entry = [line]

            elif current_date:
                # Add line to current date's entries
                current_entry.append(line)

        elif current_section == 'footer':
            footer_lines.append(line)

    # Save final entry
    if current_date and current_entry:
        entries_by_date[current_date].extend(current_entry)

    return header_lines, entries_by_date, footer_lines


def archive_old_entries(entries_by_date, today):
    """
    Archives entries older than today to dated log files in Logs/.

    Args:
        entries_by_date (dict): Dictionary mapping dates to log entries
        today (str): Today's date in YYYY-MM-DD format

    Returns:
        int: Number of dates archived
    """
    archived_count = 0

    for date, entries in entries_by_date.items():
        if date and date < today:
            # This is an old entry - archive it
            archive_path = os.path.join(LOGS_FOLDER, f"{date}.md")

            try:
                # Create archive file content
                archive_content = f"# System Log Archive - {date}\n\n"
                archive_content += f"> **Archived from:** System_Log.md\n"
                archive_content += f"> **Archive date:** {get_today_date()}\n\n"
                archive_content += "---\n\n"

                # Add the entries (skip the date header as it's in the title)
                for line in entries:
                    if not line.startswith('###'):
                        archive_content += line

                # Write to archive file
                with open(archive_path, 'w', encoding='utf-8') as f:
                    f.write(archive_content)

                print(f"✅ Archived {date} → Logs/{date}.md")
                archived_count += 1

            except Exception as e:
                print(f"⚠️  Error archiving {date}: {e}")

    return archived_count


def write_rotated_log(header_lines, today_entries, footer_lines, archived_count):
    """
    Writes the updated System_Log.md with only today's entries.

    Args:
        header_lines (list): Header section lines
        today_entries (list): Today's log entries
        footer_lines (list): Footer section lines
        archived_count (int): Number of dates that were archived
    """
    try:
        with open(SYSTEM_LOG_PATH, 'w', encoding='utf-8') as f:
            # Write header
            f.writelines(header_lines)

            # Write log rotation status
            f.write("## Log Rotation Status\n\n")
            f.write(f"- **Last Rotation:** {get_today_date()} at {datetime.now().strftime('%H:%M:%S')}\n")
            f.write(f"- **Entries Archived:** {archived_count} date(s)\n")
            f.write(f"- **Archive Location:** [Logs/](Logs/) folder\n")
            f.write(f"- **Retention:** All logs permanently archived\n\n")
            f.write("📂 [View Archived Logs](Logs/)\n\n")
            f.write("---\n\n")

            # Write activity log section
            f.write("## Activity Log\n\n")
            f.write("### Today's Activity\n\n")

            if today_entries:
                # Write today's entries (skip the date header)
                for line in today_entries:
                    if not line.startswith('###'):
                        f.write(line)
            else:
                f.write("*No activity logged today.*\n\n")

            f.write("---\n\n")

            # Write footer
            f.writelines(footer_lines)

        print(f"✅ Updated System_Log.md with rotation status")

    except Exception as e:
        print(f"❌ Error writing updated System_Log.md: {e}")


# ============================================================================
# MAIN ROTATION LOGIC
# ============================================================================

def rotate_logs():
    """
    Main log rotation function.

    Process:
    1. Create backup of current System_Log.md
    2. Read and parse System_Log.md
    3. Archive entries older than today
    4. Write updated System_Log.md with only today's entries
    """
    print("=" * 70)
    print("🔄 Bronze Tier AI Employee - Log Rotation")
    print("=" * 70)
    print(f"📅 Today: {get_today_date()}")
    print(f"📂 Logs folder: {LOGS_FOLDER}")
    print("=" * 70)
    print()

    # Step 1: Create backup
    print("📋 Step 1: Creating backup...")
    backup_path = create_backup()
    print()

    # Step 2: Read System_Log.md
    print("📖 Step 2: Reading System_Log.md...")
    header_lines, entries_by_date, footer_lines = read_system_log()

    if entries_by_date is None:
        print("❌ Failed to read System_Log.md. Aborting.")
        return

    print(f"   Found {len(entries_by_date)} date section(s)")
    print()

    # Step 3: Archive old entries
    print("📦 Step 3: Archiving old entries...")
    today = get_today_date()
    archived_count = archive_old_entries(entries_by_date, today)
    print(f"   Total archived: {archived_count} date(s)")
    print()

    # Step 4: Write updated System_Log.md
    print("✏️  Step 4: Updating System_Log.md...")
    today_entries = entries_by_date.get(today, [])
    write_rotated_log(header_lines, today_entries, footer_lines, archived_count)
    print()

    # Summary
    print("=" * 70)
    print("✅ Log Rotation Complete!")
    print("=" * 70)
    print(f"📊 Summary:")
    print(f"   - Archived: {archived_count} date(s)")
    print(f"   - Today's entries: {'Yes' if today_entries else 'None'}")
    print(f"   - Archive location: Logs/")
    if backup_path:
        print(f"   - Backup: {os.path.basename(backup_path)}")
    print("=" * 70)


# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    rotate_logs()

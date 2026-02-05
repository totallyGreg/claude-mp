#!/usr/bin/env python3
"""
OmniFocus Database Query Tool

Queries the OmniFocus SQLite database to retrieve tasks, projects, folders, and tags.

Usage:
    query_omnifocus.py --tasks [--filter STATUS]
    query_omnifocus.py --projects [--folder FOLDER]
    query_omnifocus.py --tags
    query_omnifocus.py --search QUERY
    query_omnifocus.py --due-soon [--days N]
    query_omnifocus.py --flagged
    query_omnifocus.py --today
    query_omnifocus.py --custom-query "SELECT ..."

Examples:
    # List all active tasks
    python3 query_omnifocus.py --tasks --filter active

    # Find all projects
    python3 query_omnifocus.py --projects

    # Search for tasks containing "meeting"
    python3 query_omnifocus.py --search "meeting"

    # Show tasks due in the next 7 days
    python3 query_omnifocus.py --due-soon --days 7

    # List all flagged tasks
    python3 query_omnifocus.py --flagged

    # Show today's tasks
    python3 query_omnifocus.py --today
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any


class OmniFocusDB:
    """Interface to OmniFocus SQLite database."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.

        Args:
            db_path: Optional path to OmniFocus database. If None, auto-detect.
        """
        self.db_path = db_path or self._find_database()
        if not self.db_path:
            raise FileNotFoundError(
                "Could not find OmniFocus database. "
                "Please specify path with --db-path"
            )

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def _find_database(self) -> Optional[str]:
        """Auto-detect OmniFocus database location.

        Returns:
            Path to database file, or None if not found
        """
        home = Path.home()

        # Possible OmniFocus database locations (OmniFocus 3 and 4)
        locations = [
            # OmniFocus 4
            home / "Library/Group Containers/34YW5XSRB7.com.omnigroup.OmniFocus/com.omnigroup.OmniFocus4.MacOSX/OmniFocus.ofocus/OmniFocus.sqlite",
            # OmniFocus 3
            home / "Library/Group Containers/34YW5XSRB7.com.omnigroup.OmniFocus/com.omnigroup.OmniFocus3.MacOSX/OmniFocus.ofocus/OmniFocus.sqlite",
            # Alternative structure
            home / "Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application Support/OmniFocus/OmniFocus.sqlite",
            home / "Library/Containers/com.omnigroup.OmniFocus3/Data/Library/Application Support/OmniFocus/OmniFocus.sqlite",
        ]

        for loc in locations:
            if loc.exists():
                return str(loc)

        return None

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary."""
        return {key: row[key] for key in row.keys()}

    def get_tasks(self, status_filter: str = "all") -> List[Dict[str, Any]]:
        """Get tasks from database.

        Args:
            status_filter: Filter by status - 'active', 'completed', 'dropped', or 'all'

        Returns:
            List of task dictionaries
        """
        query = """
        SELECT
            t.persistentIdentifier as id,
            t.name,
            t.dateCompleted,
            t.dateAdded,
            t.dateDue,
            t.dateDeferred,
            t.flagged,
            t.effectiveFlagged,
            t.note,
            t.estimatedMinutes,
            p.name as project,
            f.name as folder
        FROM Task t
        LEFT JOIN ProjectInfo p ON t.containingProjectInfo = p.pk
        LEFT JOIN Folder f ON p.folder = f.pk
        WHERE t.dateToStart IS NULL OR t.dateToStart <= ?
        """

        params = [datetime.now().timestamp()]

        if status_filter == "active":
            query += " AND t.dateCompleted IS NULL AND t.blocked = 0 AND t.blockedByFutureStartDate = 0"
        elif status_filter == "completed":
            query += " AND t.dateCompleted IS NOT NULL"
        elif status_filter == "dropped":
            query += " AND t.dropped = 1"

        query += " ORDER BY t.dateDue, t.effectiveFlagged DESC, t.name"

        cursor = self.conn.execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_projects(self, folder_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get projects from database.

        Args:
            folder_filter: Optional folder name to filter by

        Returns:
            List of project dictionaries
        """
        query = """
        SELECT
            p.persistentIdentifier as id,
            p.name,
            p.status,
            p.dateCompleted,
            p.dateAdded,
            p.note,
            f.name as folder,
            p.flagged,
            p.numberOfAvailableTasks,
            p.numberOfRemainingTasks
        FROM ProjectInfo p
        LEFT JOIN Folder f ON p.folder = f.pk
        WHERE p.status != 'dropped'
        """

        params = []
        if folder_filter:
            query += " AND f.name = ?"
            params.append(folder_filter)

        query += " ORDER BY f.name, p.name"

        cursor = self.conn.execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_tags(self) -> List[Dict[str, Any]]:
        """Get all tags/contexts from database.

        Returns:
            List of tag dictionaries
        """
        query = """
        SELECT
            persistentIdentifier as id,
            name,
            allowsNextAction,
            availableTaskCount
        FROM Context
        WHERE hidden = 0
        ORDER BY name
        """

        cursor = self.conn.execute(query)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def search(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for tasks by name or note.

        Args:
            search_term: Text to search for

        Returns:
            List of matching task dictionaries
        """
        query = """
        SELECT
            t.persistentIdentifier as id,
            t.name,
            t.dateCompleted,
            t.dateDue,
            t.flagged,
            t.note,
            p.name as project
        FROM Task t
        LEFT JOIN ProjectInfo p ON t.containingProjectInfo = p.pk
        WHERE (t.name LIKE ? OR t.note LIKE ?)
          AND t.dateCompleted IS NULL
        ORDER BY t.effectiveFlagged DESC, t.dateDue, t.name
        """

        search_pattern = f"%{search_term}%"
        cursor = self.conn.execute(query, [search_pattern, search_pattern])
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_due_soon(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get tasks due within specified days.

        Args:
            days: Number of days to look ahead

        Returns:
            List of task dictionaries
        """
        end_date = datetime.now() + timedelta(days=days)

        query = """
        SELECT
            t.persistentIdentifier as id,
            t.name,
            t.dateDue,
            t.flagged,
            t.note,
            p.name as project
        FROM Task t
        LEFT JOIN ProjectInfo p ON t.containingProjectInfo = p.pk
        WHERE t.dateCompleted IS NULL
          AND t.dateDue IS NOT NULL
          AND t.dateDue <= ?
        ORDER BY t.dateDue, t.effectiveFlagged DESC, t.name
        """

        cursor = self.conn.execute(query, [end_date.timestamp()])
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_flagged(self) -> List[Dict[str, Any]]:
        """Get all flagged tasks.

        Returns:
            List of flagged task dictionaries
        """
        query = """
        SELECT
            t.persistentIdentifier as id,
            t.name,
            t.dateCompleted,
            t.dateDue,
            t.note,
            p.name as project
        FROM Task t
        LEFT JOIN ProjectInfo p ON t.containingProjectInfo = p.pk
        WHERE t.effectiveFlagged = 1
          AND t.dateCompleted IS NULL
        ORDER BY t.dateDue, t.name
        """

        cursor = self.conn.execute(query)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_today(self) -> List[Dict[str, Any]]:
        """Get tasks for today (due today or deferred until today).

        Returns:
            List of task dictionaries
        """
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        query = """
        SELECT
            t.persistentIdentifier as id,
            t.name,
            t.dateDue,
            t.dateDeferred,
            t.flagged,
            t.note,
            p.name as project
        FROM Task t
        LEFT JOIN ProjectInfo p ON t.containingProjectInfo = p.pk
        WHERE t.dateCompleted IS NULL
          AND t.blocked = 0
          AND t.blockedByFutureStartDate = 0
          AND (
              (t.dateDue >= ? AND t.dateDue < ?) OR
              (t.dateDeferred >= ? AND t.dateDeferred < ?)
          )
        ORDER BY t.effectiveFlagged DESC, t.dateDue, t.name
        """

        params = [
            today_start.timestamp(), today_end.timestamp(),
            today_start.timestamp(), today_end.timestamp()
        ]

        cursor = self.conn.execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def custom_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute custom SQL query.

        Args:
            query: SQL query string

        Returns:
            List of result dictionaries
        """
        cursor = self.conn.execute(query)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def format_timestamp(ts: Optional[float]) -> Optional[str]:
    """Convert timestamp to readable date string.

    Args:
        ts: Unix timestamp

    Returns:
        Formatted date string or None
    """
    if ts is None:
        return None
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def print_tasks(tasks: List[Dict[str, Any]], show_details: bool = False):
    """Print tasks in readable format.

    Args:
        tasks: List of task dictionaries
        show_details: Whether to show full details
    """
    if not tasks:
        print("No tasks found.")
        return

    print(f"\nFound {len(tasks)} task(s):\n")

    for i, task in enumerate(tasks, 1):
        flagged = "🚩 " if task.get('flagged') or task.get('effectiveFlagged') else ""
        due = format_timestamp(task.get('dateDue'))
        due_str = f" [Due: {due}]" if due else ""
        project_str = f" ({task.get('project')})" if task.get('project') else ""

        print(f"{i}. {flagged}{task['name']}{project_str}{due_str}")

        if show_details:
            if task.get('note'):
                print(f"   Note: {task['note']}")
            if task.get('folder'):
                print(f"   Folder: {task['folder']}")
            if task.get('estimatedMinutes'):
                print(f"   Estimated: {task['estimatedMinutes']} minutes")
            print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query OmniFocus database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--db-path', help='Path to OmniFocus database')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--details', action='store_true', help='Show full details')

    # Query types
    query_group = parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument('--tasks', action='store_true', help='List tasks')
    query_group.add_argument('--projects', action='store_true', help='List projects')
    query_group.add_argument('--tags', action='store_true', help='List tags')
    query_group.add_argument('--search', metavar='QUERY', help='Search for tasks')
    query_group.add_argument('--due-soon', action='store_true', help='Tasks due soon')
    query_group.add_argument('--flagged', action='store_true', help='Flagged tasks')
    query_group.add_argument('--today', action='store_true', help='Today\'s tasks')
    query_group.add_argument('--custom-query', metavar='SQL', help='Custom SQL query')

    # Filters
    parser.add_argument('--filter', choices=['all', 'active', 'completed', 'dropped'],
                       default='active', help='Filter tasks by status')
    parser.add_argument('--folder', help='Filter projects by folder')
    parser.add_argument('--days', type=int, default=7,
                       help='Days to look ahead for due-soon (default: 7)')

    args = parser.parse_args()

    try:
        db = OmniFocusDB(args.db_path)

        # Execute query based on arguments
        if args.tasks:
            results = db.get_tasks(args.filter)
        elif args.projects:
            results = db.get_projects(args.folder)
        elif args.tags:
            results = db.get_tags()
        elif args.search:
            results = db.search(args.search)
        elif args.due_soon:
            results = db.get_due_soon(args.days)
        elif args.flagged:
            results = db.get_flagged()
        elif args.today:
            results = db.get_today()
        elif args.custom_query:
            results = db.custom_query(args.custom_query)
        else:
            results = []

        # Output results
        if args.json:
            # Convert timestamps to readable dates for JSON output
            for result in results:
                for key in ['dateDue', 'dateCompleted', 'dateAdded', 'dateDeferred']:
                    if key in result and result[key]:
                        result[key] = format_timestamp(result[key])
            print(json.dumps(results, indent=2))
        else:
            if args.projects:
                print(f"\nFound {len(results)} project(s):\n")
                for proj in results:
                    status = f" [{proj['status']}]" if proj.get('status') else ""
                    folder = f" ({proj['folder']})" if proj.get('folder') else ""
                    tasks_info = f" [{proj.get('numberOfAvailableTasks', 0)} available]"
                    print(f"• {proj['name']}{folder}{status}{tasks_info}")
            elif args.tags:
                print(f"\nFound {len(results)} tag(s):\n")
                for tag in results:
                    count = f" [{tag.get('availableTaskCount', 0)} tasks]"
                    print(f"• {tag['name']}{count}")
            else:
                print_tasks(results, args.details)

        db.close()

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

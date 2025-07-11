#!/usr/bin/env python
"""Database Table Copy Script

Copies specified tables from a source SQLite database to the intake-crm.db database.
Handles schema creation and data copying with options for different copy modes.
"""
import argparse
import sqlite3
import sys
from pathlib import Path
from typing import List, Tuple


def get_table_schema(conn: sqlite3.Connection, table_name: str) -> str:
    """Get the CREATE TABLE statement for a table."""
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        raise ValueError(f"Table '{table_name}' not found in source database")


def get_table_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    """Get list of column names for a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return [col[1] for col in columns]  # col[1] is the column name


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Check if a table exists in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None


def get_row_count(conn: sqlite3.Connection, table_name: str) -> int:
    """Get the number of rows in a table."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cursor.fetchone()[0]


def copy_table_data(source_conn: sqlite3.Connection, dest_conn: sqlite3.Connection, 
                   table_name: str, mode: str = "replace") -> Tuple[int, int]:
    """Copy data from source table to destination table.
    
    Args:
        source_conn: Source database connection
        dest_conn: Destination database connection
        table_name: Name of the table to copy
        mode: Copy mode - 'replace', 'append', or 'skip_existing'
    
    Returns:
        Tuple of (rows_copied, rows_skipped)
    """
    source_cursor = source_conn.cursor()
    dest_cursor = dest_conn.cursor()
    
    # Get all data from source table
    source_cursor.execute(f"SELECT * FROM {table_name}")
    rows = source_cursor.fetchall()
    
    if not rows:
        print(f"   📊 Source table '{table_name}' is empty")
        return 0, 0
    
    # Get column names
    columns = get_table_columns(source_conn, table_name)
    column_list = ", ".join(columns)
    placeholders = ", ".join(["?" for _ in columns])
    
    rows_copied = 0
    rows_skipped = 0
    
    if mode == "replace":
        # Clear destination table first
        dest_cursor.execute(f"DELETE FROM {table_name}")
        
        # Insert all rows
        dest_cursor.executemany(f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})", rows)
        rows_copied = len(rows)
        
    elif mode == "append":
        # Just insert all rows (may cause conflicts if there are unique constraints)
        try:
            dest_cursor.executemany(f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})", rows)
            rows_copied = len(rows)
        except sqlite3.IntegrityError as e:
            # Try inserting one by one to count successes/failures
            for row in rows:
                try:
                    dest_cursor.execute(f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})", row)
                    rows_copied += 1
                except sqlite3.IntegrityError:
                    rows_skipped += 1
    
    elif mode == "skip_existing":
        # Use INSERT OR IGNORE to skip existing rows
        dest_cursor.executemany(f"INSERT OR IGNORE INTO {table_name} ({column_list}) VALUES ({placeholders})", rows)
        rows_copied = dest_cursor.rowcount
        rows_skipped = len(rows) - rows_copied
    
    dest_conn.commit()
    return rows_copied, rows_skipped


def copy_table(source_db: Path, dest_db: Path, table_name: str, mode: str = "replace", 
               create_if_missing: bool = True) -> bool:
    """Copy a single table from source to destination database."""
    
    print(f"\n📋 Processing table: {table_name}")
    
    # Connect to databases
    try:
        source_conn = sqlite3.connect(source_db)
        dest_conn = sqlite3.connect(dest_db)
    except Exception as e:
        print(f"❌ Failed to connect to databases: {e}")
        return False
    
    try:
        # Check if source table exists
        if not table_exists(source_conn, table_name):
            print(f"❌ Table '{table_name}' not found in source database")
            return False
        
        # Get source table info
        source_count = get_row_count(source_conn, table_name)
        print(f"   📊 Source rows: {source_count}")
        
        # Check if destination table exists
        dest_exists = table_exists(dest_conn, table_name)
        
        if not dest_exists:
            if create_if_missing:
                print(f"   🔧 Creating table '{table_name}' in destination...")
                schema = get_table_schema(source_conn, table_name)
                dest_conn.execute(schema)
                dest_conn.commit()
                print(f"   ✅ Table created")
            else:
                print(f"❌ Table '{table_name}' not found in destination database")
                return False
        else:
            dest_count = get_row_count(dest_conn, table_name)
            print(f"   📊 Destination rows (before): {dest_count}")
        
        # Copy data
        print(f"   🔄 Copying data (mode: {mode})...")
        rows_copied, rows_skipped = copy_table_data(source_conn, dest_conn, table_name, mode)
        
        # Show results
        final_count = get_row_count(dest_conn, table_name)
        print(f"   ✅ Copy complete:")
        print(f"      Rows copied: {rows_copied}")
        print(f"      Rows skipped: {rows_skipped}")
        print(f"      Final count: {final_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error copying table '{table_name}': {e}")
        return False
    
    finally:
        source_conn.close()
        dest_conn.close()


def list_tables(db_path: Path) -> List[str]:
    """List all tables in a database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def main():
    parser = argparse.ArgumentParser(description="Copy tables between SQLite databases")
    parser.add_argument("source_db", help="Path to source database file")
    parser.add_argument("--dest-db", default="intake-crm.db", help="Path to destination database (default: intake-crm.db)")
    parser.add_argument("--tables", nargs="+", help="Table names to copy (space-separated)")
    parser.add_argument("--list-tables", action="store_true", help="List all tables in source database")
    parser.add_argument("--mode", choices=["replace", "append", "skip_existing"], default="replace",
                       help="Copy mode: replace (clear dest first), append (add to dest), skip_existing (ignore duplicates)")
    parser.add_argument("--no-create", action="store_true", help="Don't create tables if they don't exist in destination")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied without actually doing it")
    
    args = parser.parse_args()
    
    source_db = Path(args.source_db)
    dest_db = Path(args.dest_db)
    
    # Validate source database
    if not source_db.exists():
        print(f"❌ Source database not found: {source_db}")
        return
    
    print(f"📁 Source database: {source_db}")
    print(f"📁 Destination database: {dest_db}")
    
    # List tables if requested
    if args.list_tables:
        print(f"\n📋 Tables in source database:")
        tables = list_tables(source_db)
        for i, table in enumerate(tables, 1):
            conn = sqlite3.connect(source_db)
            count = get_row_count(conn, table)
            conn.close()
            print(f"   {i}. {table} ({count} rows)")
        return
    
    # Validate table names
    if not args.tables:
        print("❌ No tables specified. Use --tables to specify table names or --list-tables to see available tables.")
        return
    
    # Check if destination database exists
    if not dest_db.exists():
        print(f"⚠️  Destination database doesn't exist. Creating: {dest_db}")
        # Create empty database
        conn = sqlite3.connect(dest_db)
        conn.close()
    
    if args.dry_run:
        print(f"\n🔍 DRY RUN - Would copy these tables:")
        for table in args.tables:
            print(f"   - {table} (mode: {args.mode})")
        return
    
    print(f"\n🚀 Starting table copy operation...")
    print(f"   Mode: {args.mode}")
    print(f"   Tables: {', '.join(args.tables)}")
    
    # Copy each table
    success_count = 0
    for table in args.tables:
        if copy_table(source_db, dest_db, table, args.mode, not args.no_create):
            success_count += 1
    
    # Summary
    print(f"\n📊 Copy Summary:")
    print(f"   Total tables: {len(args.tables)}")
    print(f"   Successfully copied: {success_count}")
    print(f"   Failed: {len(args.tables) - success_count}")
    
    if success_count == len(args.tables):
        print(f"✅ All tables copied successfully!")
    else:
        print(f"⚠️  Some tables failed to copy")


if __name__ == "__main__":
    main()
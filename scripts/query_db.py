#!/usr/bin/env python
"""Database Query Helper Script

Simple utility to query the intake-crm database and explore the data.
"""
import argparse
import sqlite3
import sys
from pathlib import Path

# Add repository root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def query_database(db_path: Path, query: str = None):
    """Query the database and display results."""
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if query:
        # Execute custom query
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            print(f"\n📊 Query Results ({len(results)} rows):")
            print("=" * 80)
            
            # Print column headers
            print(" | ".join(columns))
            print("-" * 80)
            
            # Print results
            for row in results:
                print(" | ".join(str(cell) if cell is not None else "NULL" for cell in row))
                
        except Exception as e:
            print(f"❌ Query failed: {e}")
    else:
        # Show database overview
        print(f"📊 Database Overview: {db_path}")
        print("=" * 50)
        
        # Show table schemas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Table: {table_name}")
            print("-" * 30)
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                print(f"  {col_name} ({col_type}){' NOT NULL' if not_null else ''}{' PRIMARY KEY' if pk else ''}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  Rows: {count}")
    
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the intake-crm database")
    parser.add_argument("--db-path", type=str, default="intake-crm.db", help="Path to SQLite database file")
    parser.add_argument("--query", type=str, help="SQL query to execute")
    parser.add_argument("--list-referrals", action="store_true", help="List all referrals")
    parser.add_argument("--count", action="store_true", help="Show counts by status")
    args = parser.parse_args()

    db_path = Path(args.db_path)
    
    if args.query:
        query_database(db_path, args.query)
    elif args.list_referrals:
        query_database(db_path, "SELECT id, patient_name, order_number, priority, created_at FROM referrals ORDER BY created_at DESC LIMIT 20")
    elif args.count:
        query_database(db_path, """
            SELECT 
                referral,
                COUNT(*) as count,
                COUNT(CASE WHEN priority = 'Urgent' THEN 1 END) as urgent_count
            FROM referrals 
            GROUP BY referral
        """)
    else:
        query_database(db_path)


if __name__ == "__main__":
    main() 
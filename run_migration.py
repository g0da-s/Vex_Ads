"""
Simple script to run database migrations on Supabase.
"""

import os
from pathlib import Path
from supabase import create_client, Client
from config import get_settings

settings = get_settings()

def run_migration(migration_file: str):
    """
    Run a SQL migration file against the Supabase database.

    Args:
        migration_file: Path to the .sql file
    """
    # Create Supabase client
    supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

    # Read migration file
    migration_path = Path(migration_file)
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return

    sql_content = migration_path.read_text()

    print(f"🔄 Running migration: {migration_path.name}")
    print(f"SQL:\n{sql_content}\n")

    try:
        # Execute SQL via Supabase's RPC or direct SQL execution
        # Note: Supabase Python client doesn't have direct SQL execution
        # You need to run this via the Supabase dashboard or use psycopg2
        print("⚠️  Note: Supabase Python client doesn't support direct SQL execution.")
        print("Please run this migration via:")
        print("1. Supabase Dashboard -> SQL Editor")
        print("2. Or use psycopg2 with your database connection string")
        print("\nSQL to execute:")
        print("-" * 60)
        print(sql_content)
        print("-" * 60)

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    # Run the template_version migration
    run_migration("migrations/001_add_template_version.sql")

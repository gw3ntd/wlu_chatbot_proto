"""
Migration script to add the 'resolved' column to the Conversations table.
This script should be run once to update existing databases.
"""

from sqlalchemy import text
from ucr_chatbot.db.models import engine, Session


def migrate_add_resolved_column():
    """Add the resolved column to the Conversations table if it doesn't exist."""

    with Session(engine) as session:
        try:
            # Check if the column already exists
            result = session.execute(
                text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'Conversations' 
                AND column_name = 'resolved'
            """)
            )

            if not result.fetchone():
                # Add the resolved column with default value False
                session.execute(
                    text("""
                    ALTER TABLE "Conversations" 
                    ADD COLUMN resolved BOOLEAN NOT NULL DEFAULT FALSE
                """)
                )
                session.commit()
                print("✅ Successfully added 'resolved' column to Conversations table")
            else:
                print("ℹ️  'resolved' column already exists in Conversations table")

        except Exception as e:
            session.rollback()
            print(f"❌ Error adding 'resolved' column: {e}")
            raise


if __name__ == "__main__":
    print("Starting migration to add 'resolved' column to Conversations table...")
    migrate_add_resolved_column()
    print("Migration completed!")

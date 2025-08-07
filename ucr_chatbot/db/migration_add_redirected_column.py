"""
Migration script to add the 'redirected' column to the Conversations table.
This script should be run once to update existing databases.
"""

from sqlalchemy import text
from ucr_chatbot.db.models import engine, Session


def migrate_add_redirected_column():
    """Add the redirected column to the Conversations table if it doesn't exist."""

    with Session(engine) as session:
        try:
            # Check if the column already exists
            result = session.execute(
                text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'Conversations' 
                AND column_name = 'redirected'
            """)
            )

            if not result.fetchone():
                # Add the redirected column with default value False
                session.execute(
                    text("""
                    ALTER TABLE "Conversations" 
                    ADD COLUMN redirected BOOLEAN NOT NULL DEFAULT FALSE
                """)
                )
                session.commit()
                print(
                    "✅ Successfully added 'redirected' column to Conversations table"
                )
            else:
                print("ℹ️  'redirected' column already exists in Conversations table")

        except Exception as e:
            session.rollback()
            print(f"❌ Error adding 'redirected' column: {e}")
            raise


if __name__ == "__main__":
    print("Starting migration to add 'redirected' column to Conversations table...")
    migrate_add_redirected_column()
    print("Migration completed!")

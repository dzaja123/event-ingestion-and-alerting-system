import logging
import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from alembic.config import Config
from alembic import command
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_sync_database_url():
    """Convert async database URL to sync for migrations."""
    async_url = settings.ASYNC_SQLALCHEMY_DATABASE_URI
    # Replace asyncpg with psycopg2 for synchronous operations
    sync_url = async_url.replace("postgresql+asyncpg://", "postgresql://")
    return sync_url


def run_migrations():
    """Run database migrations."""
    try:
        logger.info("Starting database migrations...")
        
        # Create Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Set the database URL for migrations
        sync_url = get_sync_database_url()
        alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


def create_initial_migration():
    """Create initial migration if none exist."""
    try:
        alembic_cfg = Config("alembic.ini")
        
        # Set the database URL for migrations
        sync_url = get_sync_database_url()
        alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
        
        # Check if migrations directory has any version files
        versions_dir = Path("migrations/versions")
        if not any(versions_dir.glob("*.py")):
            logger.info("No migrations found, creating initial migration...")
            command.revision(alembic_cfg, autogenerate=True, message="Initial migration")
            logger.info("Initial migration created!")
        else:
            logger.info("Migrations already exist, skipping creation.")
            
    except Exception as e:
        logger.error(f"Failed to create initial migration: {e}")
        sys.exit(1)


def main():
    """Main migration function."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "create":
            create_initial_migration()
        elif sys.argv[1] == "upgrade":
            run_migrations()
        else:
            logger.error("Usage: python migrate.py [create|upgrade]")
            sys.exit(1)
    else:
        run_migrations()


if __name__ == "__main__":
    main()

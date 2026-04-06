"""Create tables and seed default admin user. Run once after DB is up."""
import asyncio
import os
import sys

# Add parent so app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings
from app.database import Base, AsyncSessionLocal, engine
from app.models.user import User, UserRole
from app.core.security import hash_password
from sqlalchemy import select


async def init():
    settings = get_settings()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@123")
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(User).where(User.email == admin_email))
        if r.scalar_one_or_none():
            print("Admin user already exists.")
            return
        admin = User(
            email=admin_email,
            hashed_password=hash_password(admin_password),
            full_name="Administrator",
            role=UserRole.ADMIN,
        )
        db.add(admin)
        await db.commit()
        print(f"Created admin user: {admin_email}")


if __name__ == "__main__":
    asyncio.run(init())

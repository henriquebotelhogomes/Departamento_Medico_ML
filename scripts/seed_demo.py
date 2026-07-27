"""Seed the demo user without starting the API.

    cd backend && uv run python ../scripts/seed_demo.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow running from the repository root: make the backend package importable.
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


async def _main() -> None:
    from app.db.base import Base
    from app.db.session import AsyncSessionLocal, engine
    from app.seed import seed_demo_user

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed_demo_user(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
    print("[ok] Demo user ready.")

from pathlib import Path
import asyncio

from sqlalchemy import text

from db.session import engine


SQL_DIR = Path("sql/postgres")


async def main() -> None:
    files = sorted(SQL_DIR.glob("*.sql"))
    async with engine.begin() as conn:
        for path in files:
            sql = path.read_text()
            await conn.execute(text(sql))
            print(f"applied {path.name}")


if __name__ == "__main__":
    asyncio.run(main())
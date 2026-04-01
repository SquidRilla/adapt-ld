import asyncio
from app.core.database import init_db, seed_data

async def main():
    await init_db()
    await seed_data()
    print("Database initialized and seeded.")

if __name__ == "__main__":
    asyncio.run(main())
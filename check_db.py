import asyncio
from app.core.database import AsyncSessionLocal, AttentionResult

async def check_attention():
    async with AsyncSessionLocal() as db:
        results = await db.execute(db.query(AttentionResult))
        for r in results.scalars():
            print(r.__dict__)

if __name__ == "__main__":
    asyncio.run(check_attention())
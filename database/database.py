from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI, DB_NAME

client = AsyncIOMotorClient(DB_URI)
db = client[DB_NAME]
processed = db["processed_items"]


async def save_processed(data: dict):
    await processed.insert_one(data) 
    

async def is_processed(url: str) -> bool:
    doc = await processed.find_one({"url": url})
    return doc is not None 





from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI, DB_NAME

client = AsyncIOMotorClient(DB_URI)
db = client[DB_NAME]
processed = db["processed_items"]
upcoming_posts = db['upcoming_posts']


async def save_processed(data: dict):
    await processed.insert_one(data) 
    

async def is_processed(url: str) -> bool:
    doc = await processed.find_one({"url": url})
    return doc is not None 


async def add_post(post_data: dict):
    """Add a new post to MongoDB"""
    await upcoming_posts.insert_one(post_data)
    return True

async def get_oldest_post():
    """Get the oldest post from DB"""
    post = await upcoming_posts.find_one(sort=[("_id", 1)])
    return post

# Fetch all waiting posts
async def get_all_posts():
    return await upcoming_posts.find().to_list(length=50)  # limit to 50 for safety


async def delete_post(post_id):
    """Delete post by its _id"""
    await upcoming_posts.delete_one({"_id": post_id})
    return True


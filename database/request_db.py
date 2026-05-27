from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI, DATABASE_NAME

client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]

request_col = db["movie_requests"]

async def save_request(movie, chat_id):
    await request_col.update_one(
        {"movie": movie.lower()},
        {
            "$set": {
                "movie": movie.lower(),
                "chat_id": chat_id
            }
        },
        upsert=True
    )

async def get_request(movie):
    return await request_col.find_one({"movie": movie.lower()})

async def delete_request(movie):
    await request_col.delete_one({"movie": movie.lower()})
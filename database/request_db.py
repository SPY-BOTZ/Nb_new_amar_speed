from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI, DATABASE_NAME

client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]

request_col = db["movie_requests"]

async def save_request(movie, user_id):
    movie = movie.lower().strip()

    data = await request_col.find_one({"movie": movie})

    if data:
        if user_id not in data.get("users", []):
            await request_col.update_one(
                {"movie": movie},
                {"$push": {"users": user_id}}
            )
    else:
        await request_col.insert_one({
            "movie": movie,
            "users": [user_id]
        })

async def get_request(movie):
    movie = movie.lower().strip()
    return await request_col.find_one({"movie": movie})

async def delete_request(movie):
    movie = movie.lower().strip()
    await request_col.delete_one({"movie": movie})

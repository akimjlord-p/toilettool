from fastapi import FastAPI

from app.api.v1 import users, toilets, reviews, top

app = FastAPI(title="ToiletTool API", version="1.0.0")

app.include_router(users.router, prefix="/api/v1")
app.include_router(toilets.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(top.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

@router.get("/api/status")
async def status():
    return {"status": "ok"}

@router.get("/api/test")
async def test():
    return {"test": "hello"}

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "root"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

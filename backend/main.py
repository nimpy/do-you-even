from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from api_endpoints import router as http_router


app = FastAPI()
app.include_router(http_router)
origins = [
    "http://localhost",
    "http://0.0.0.0",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

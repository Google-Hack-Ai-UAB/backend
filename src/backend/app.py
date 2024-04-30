# STL
import logging

# PDM
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# LOCAL
from backend.JobRoutes import JobRouter
from backend.ChatRoutes import ChatRouter

app = FastAPI()

origins = ["*"]

logging.basicConfig(level=logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(JobRouter)
app.include_router(ChatRouter)
load_dotenv()

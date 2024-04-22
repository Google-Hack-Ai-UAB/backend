# PDM
import json
import tempfile
from tempfile import NamedTemporaryFile

from bson.objectid import ObjectId
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (FileResponse, JSONResponse, Response,
                               StreamingResponse)
from gridfs import GridFS
from pymongo import errors

from backend.Models import ReadResume
from backend.mongo import init_mongo
from backend.utils import convert_pdf_to_png, store_pdf

student_router = APIRouter()


@student_router.post("/upload")
async def upload(resume: UploadFile = File(...)):
    client = init_mongo()
    db = client["ai"]

    pdf = await resume.read()

    email = "test"

    pdf_collection = db["pdfs"]
    pdf_collection.insert_one({"user": email, "pdf": pdf})

    user_collection = db["users"]
    user_collection.insert_one({"_id": email})


@student_router.post("/resume/query")
async def read(query: ReadResume):
    try:
        user = query.user

        client = init_mongo()
        db = client["ai"]
        pdf_collection = db["pdfs"]

        result = pdf_collection.find({"user": user})

        pdfs = [document.get("pdf") for document in result]

        if pdfs:
            return Response(content=pdfs[0], media_type="application/pdf")
        else:
            return {"message": "No PDF found for the user"}

    except Exception as e:
        return {"error": str(e)}

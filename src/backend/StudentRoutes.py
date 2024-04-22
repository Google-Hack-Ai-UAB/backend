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

from backend.mongo import init_mongo
from backend.utils import convert_pdf_to_png, store_pdf

student_router = APIRouter()


@student_router.post("/upload")
async def upload(resume: UploadFile = File(...)):
    client = init_mongo()
    db = client["recruit_tracker"]

    pdf = await resume.read()

    email = "test"

    pdf_ID = store_pdf(db, pdf, email)  # store pdf in db

    user_collection = db["users"]
    user_collection.update_one({"_id": email}, {"$set": {"pdf_ID": str(pdf_ID)}})


@student_router.post("/student/resume")
async def resume(request: Request):
    json_data = await request.json()
    user = json_data["user"]
    email = user["email"]

    client = init_mongo(URL)
    db = client["recruit_tracker"]
    user_collection = db["users"]

    # Retrieve PDF ID from user document
    user_doc = user_collection.find_one({"_id": email})
    print(user_doc)
    pdf_ID = user_doc.get("pdf_ID")

    if not pdf_ID:
        return {"error": "PDF not found for the user."}

    # Initialize GridFS
    fs = GridFS(db, collection="pdfs")

    file_obj = fs.get(ObjectId(pdf_ID))

    if file_obj is None:
        return {"error": "PDF not found in GridFS."}

    # Retrieve the binary content of the PDF
    pdf_binary = file_obj.read()

    # Write binary content to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(pdf_binary)

        # Convert the PDF to another format if needed
        # Example: converting to PNG using PyPDF2
        convert_pdf_to_png(temp_file.name)

        # Set Content-Disposition header with filename
        headers = {"Content-Disposition": f'attachment; filename="resume.pdf"'}

        # Return the file as a response
        with open(temp_file.name, "rb") as output_file:
            return StreamingResponse(
                output_file, media_type="application/pdf", headers=headers
            )


@student_router.post("/student/query")
async def read(request: Request):
    try:
        request_json = await request.json()
        filter_conditions = request_json.get("filter", {})
        print(f"FILTER CONDITIONS: {filter_conditions}")

        if filter_conditions is None:
            filter_conditions = {}

        filter_conditions["role"] = "student"

        client = init_mongo(URL)
        db = client["recruit_tracker"]
        user_collection = db["users"]

        if filter_conditions:
            result = user_collection.find(filter_conditions)
        else:
            print("running here")
            result = user_collection.find({})

        result_list = list(result)

        for user in result_list:
            user["_id"] = str(user["_id"])

        client.close()

        return JSONResponse(content={"users": result_list}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

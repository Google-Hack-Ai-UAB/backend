# PDM
import json
import tempfile
from tempfile import NamedTemporaryFile

from bson.objectid import ObjectId
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import (FileResponse, JSONResponse, Response,
                               StreamingResponse)
from gridfs import GridFS
from openai import OpenAI
from pymongo import errors

import recruit_tracker_api.utils as utils
from recruit_tracker_api.constants import MONGO_URL as url
from recruit_tracker_api.constants import OPENAI_API_KEY
from recruit_tracker_api.mongo import init_mongo
from fastapi.middleware.cors import CORSMiddleware

student_router = APIRouter()

client = OpenAI(api_key=OPENAI_API_KEY)


# app = student_router

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost", "http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

@student_router.post("/upload")
async def upload(email: str = Form(...), resume: UploadFile = File(...)):
    client = init_mongo(url)
    db = client["recruit_tracker"]

    pdf = await resume.read()

    pdf_ID = utils.store_pdf(db, pdf, email)  # store pdf in db

    user_collection = db["users"]
    user_collection.update_one({"_id": email}, {"$set": {"pdf_ID": str(pdf_ID)}})


@student_router.post("/student/resume")
async def resume(request: Request):
    json_data = await request.json()
    user = json_data["user"]
    email = user["email"]

    client = init_mongo(url)
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
        utils.convert_pdf_to_png(temp_file.name)

        # Set Content-Disposition header with filename
        headers = {"Content-Disposition": f'attachment; filename="resume.pdf"'}

        # Return the file as a response
        with open(temp_file.name, 'rb') as output_file:
            return StreamingResponse(output_file, media_type="application/pdf", headers=headers)



@student_router.post("/student/query")
async def read(request: Request):
    try:
        request_json = await request.json()
        filter_conditions = request_json.get("filter", {})
        print(f"FILTER CONDITIONS: {filter_conditions}")

        if filter_conditions is None:
            filter_conditions = {}

        filter_conditions["role"] = "student"
        print(filter_conditions)

        client = init_mongo(url)
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

        print(result_list)

        return JSONResponse(content={"users": result_list}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@student_router.post("/student")
async def create(request: Request):
    try:
        json = await request.json()
        user = json["user"]

        assert user.get("email")

        client = init_mongo(url)
        db = client["recruit_tracker"]
        user_collection = db["users"]

        # hash password
        hash_pw = utils.hash_password(user.get("password"))
        user["password"] = hash_pw
        user["role"] = "student"

        user["resume_hash"] = ""

        # print(user)
        user_collection.insert_one({"_id": user.get("email"), **user})

        client.close()
        return JSONResponse(content={"creation": str("success")}, status_code=200)

    except errors.DuplicateKeyError:
        return JSONResponse(
            content={"error": "Account with that email already exists."},
            status_code=409,
        )

    except Exception as e:
        print(e)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@student_router.post("/student/update")
async def update(request: Request):
    try:
        json = await request.json()
        user = json["user"]
        assert user.get("email")

        client = init_mongo(url)
        db = client["recruit_tracker"]
        user_collection = db["users"]

        user_collection.update_one({"_id": user.get("email")}, {"$set": {**user}})
        client.close()

        return JSONResponse(content={"update": "success"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@student_router.post("/student/delete")
async def delete(request: Request):
    try:
        json = await request.json()
        user = json["user"]
        assert user.get("email")

        client = init_mongo(url)
        db = client["recruit_tracker"]
        user_collection = db["users"]

        user_collection.delete_one({"_id": user.get("email")})
        return JSONResponse(content={"update": "success"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=200)


@student_router.post("/api/login")
async def login(request: Request):
    try:
        json_data = await request.json()
        user = json_data.get("user")

        assert (
            user and user.get("email") and user.get("password")
        ), "Email and password are required."

        client = init_mongo(url)
        db = client["recruit_tracker"]
        user_collection = db["users"]

        user_email = user.get("email")

        result = user_collection.find_one({"email": user_email})

        if not result:
            raise HTTPException(status_code=401, detail="Email not found.")

        if not utils.verify_password(user.get("password"), result.get("password")):
            raise HTTPException(
                status_code=401, detail="Password does not match email."
            )

        # success
        token = utils.create_jwt_token(user, db)

        return JSONResponse(
            content={"login": "Login successful!", "token": token}, status_code=200
        )

    except HTTPException as he:
        return JSONResponse(
            content={"login": str(he.detail)}, status_code=he.status_code
        )

    except AssertionError as ae:
        return JSONResponse(content={"error": str(ae)}, status_code=400)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@student_router.post("/api/testgpt")
async def test_gpt(request: Request):
    request_json = await request.json()
    user_input = request_json["data"]

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a programming devops expert",
            },
            {
                "role": "user",
                "content": user_input,  # Use the extracted user input
            },
        ],
    )

    text = completion.choices[0].message  # Extract the text from the completion
    return {"text": text}
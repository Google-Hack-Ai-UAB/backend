# PDM
import logging

import requests
from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import Response

from backend.constants import DOMAIN
from backend.Models import ReadResume
from backend.mongo import get_cursor, init_mongo
from backend.utils import oauth2_scheme

student_router = APIRouter()

LOG = logging.getLogger(__name__)


@student_router.get("/user")
def get_user(token_payload: str = Depends(oauth2_scheme)):
    response = requests.get(
        f"https://{DOMAIN}/userinfo",
        headers={"Authorization": f"Bearer {token_payload}"},
    )

    user_data = response.json()
    LOG.debug(f"User Data: {user_data}")

    cursor = get_cursor("ai", "users")
    user = cursor.find_one({"email": user_data["email"]})

    if user:
        user.pop("_id")
        user.pop("userId")

    return {"userData": user}


@student_router.get("/applicant")
def get_profile(token_payload: str = Depends(oauth2_scheme)):
    response = requests.get(
        f"https://{DOMAIN}/userinfo",
        headers={"Authorization": f"Bearer {token_payload}"},
    )

    user_data = response.json()
    LOG.debug(f"User Data: {user_data}")

    cursor = get_cursor("ai", "users")
    user = cursor.find_one({"email": user_data["email"]})

    if user:
        user.pop("_id")
        user.pop("userId")

    cursor = get_cursor("ai", "pdfs")
    pdf = cursor.find_one({"user": user_data["email"]})

    # if pdf and user:
    #     user["pdf"] = pdf["filename"]

    return {"userData": user}


@student_router.post("/applicant")
async def update_profile(request: Request, token_payload: str = Depends(oauth2_scheme)):
    user = await request.json()
    filter = {"email": user["email"]}
    new_values = {"$set": {**user}}

    cursor = get_cursor("ai", "users")
    cursor.update_one(filter, new_values)

    print(f"Request: {await request.json()}")


@student_router.post("/upload")
async def upload(
    resume: UploadFile = File(...), token_payload: str = Depends(oauth2_scheme)
):
    response = requests.get(
        f"https://{DOMAIN}/userinfo",
        headers={"Authorization": f"Bearer {token_payload}"},
    )

    user_data = response.json()

    client = init_mongo()
    db = client["ai"]

    pdf = await resume.read()

    pdf_collection = db["pdfs"]
    pdf_collection.insert_one(
        {"user": user_data["email"], "pdf": pdf, "filename": resume.filename}
    )


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


@student_router.get("/jobs")
async def read_jobs():
    try:
        cursor = get_cursor("ai", "jobs")
        jobs = []

        for document in cursor.find().limit(10):
            document.pop("recruiter")
            document.pop("_id")
            jobs.append(document)

        return {"jobs": jobs}
    except Exception as e:
        return {"error": e}

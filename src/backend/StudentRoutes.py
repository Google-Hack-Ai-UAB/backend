# PDM

from types import new_class

import requests
from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import Response

from backend.constants import DOMAIN
from backend.Models import ReadResume
from backend.mongo import get_cursor, init_mongo
from backend.utils import oauth2_scheme

student_router = APIRouter()


@student_router.get("/applicant")
def get_profile(token_payload: str = Depends(oauth2_scheme)):
    response = requests.get(
        f"https://{DOMAIN}/userinfo",
        headers={"Authorization": f"Bearer {token_payload}"},
    )

    user_data = response.json()
    cursor = get_cursor("ai", "users")
    user = cursor.find_one({"email": user_data["email"]})

    if user:
        user.pop("_id")
        user.pop("userId")

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

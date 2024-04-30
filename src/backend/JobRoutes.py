# STL
import logging
from datetime import datetime

# PDM
import requests
from fastapi import File, Depends, Request, APIRouter, UploadFile
from bson.objectid import ObjectId
from fastapi.responses import Response, JSONResponse

# LOCAL
from backend.mongo import get_cursor, init_mongo
from backend.utils import oauth2_scheme, get_user_document
from backend.Models import ReadResume, ApplyForJob, CreateComment, GatherComment
from backend.constants import DOMAIN

JobRouter = APIRouter()

LOG = logging.getLogger(__name__)


@JobRouter.get("/user")
def get_user(token_payload: str = Depends(oauth2_scheme)):
    user = get_user_document(token_payload=token_payload, trim_ids=True)

    return {"userData": user}


@JobRouter.get("/applicant")
def get_profile(token_payload: str = Depends(oauth2_scheme)):
    user = get_user_document(token_payload=token_payload, trim_ids=True)

    if user:
        cursor = get_cursor("ai", "pdfs")
        pdf = cursor.find_one({"user": user["email"]})

        if pdf and user:
            user["pdf"] = pdf["filename"]

        return {"userData": user}


@JobRouter.post("/applicant")
async def update_profile(request: Request):
    user = await request.json()
    filter = {"email": user["email"]}
    new_values = {"$set": {**user}}

    try:
        cursor = get_cursor("ai", "users")
        cursor.update_one(filter, new_values)
    except Exception as e:
        return JSONResponse({"error": e}, status_code=501)


@JobRouter.post("/upload")
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

    return JSONResponse(content={"message": "success"})


@JobRouter.post("/resume/query")
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
        JSONResponse(content={"error": str(e)}, status_code=501)


@JobRouter.get("/jobs")
async def read_jobs():
    try:
        cursor = get_cursor("ai", "jobs")
        jobs = []

        for document in cursor.find().limit(10):
            document.pop("recruiter")
            document["_id"] = str(document["_id"])
            jobs.append(document)

        return {"jobs": jobs}

    except Exception as e:
        return JSONResponse(content={"error": e}, status_code=501)


@JobRouter.post("/apply")
async def apply_job(
    submitted_job: ApplyForJob, token_payload: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_document(token_payload=token_payload)
        cursor = get_cursor("ai", "jobs")

        job = cursor.find_one({"_id": ObjectId(submitted_job.job_id)})
        cursor = get_cursor("ai", "applications")

        if user and job:
            cursor.insert_one(
                {
                    "applicant": ObjectId(user["_id"]),
                    "job": ObjectId(job["_id"]),
                    "timeCreated": datetime.now(),
                    "status": "Applied",
                    "company": job["company"],
                    "recruiterComments": [],
                    "applicantComments": [],
                }
            )

    except Exception as e:
        return JSONResponse(content={"error": e}, status_code=501)


@JobRouter.get("/applied_jobs")
async def get_job_status(token_payload: str = Depends(oauth2_scheme)):
    try:
        user = get_user_document(token_payload=token_payload)
        cursor = get_cursor("ai", "applications")

        if user:
            applications = [
                application for application in cursor.find({"applicant": user["_id"]})
            ]

            cursor = get_cursor("ai", "jobs")
            pdf_cursor = get_cursor("ai", "pdfs")

            pdf = pdf_cursor.find_one({"user": user["email"]}) if user else None
            if not pdf:
                pdf = dict()

            applied_jobs = []
            for application in applications:
                job = cursor.find_one({"_id": application["job"]})
                if job:
                    applied_jobs.append(
                        {
                            "jobId": str(job["_id"]),
                            "applicationId": str(application["_id"]),
                            "fullName": user["fullName"],
                            "applicantEmail": user["email"],
                            "jobTitle": job["job_title"],
                            "company": job.get("company"),
                            "timeCreated": application["timeCreated"],
                            "status": application["status"],
                            "userResume": {
                                "filename": pdf.get("filename"),
                            },
                        }
                    )
            return {"jobs": applied_jobs}

    except Exception as e:
        return JSONResponse(content={"error": e}, status_code=501)


@JobRouter.get("/recruiter_jobs")
async def get_recruiter_jobs(token_payload: str = Depends(oauth2_scheme)):
    try:
        user = get_user_document(token_payload=token_payload)
        application_cursor = get_cursor("ai", "applications")

        if user:
            applications = [
                application
                for application in application_cursor.find({"company": user["company"]})
            ]

            job_cursor = get_cursor("ai", "jobs")
            user_cursor = get_cursor("ai", "users")
            pdf_cursor = get_cursor("ai", "pdfs")

            applied_jobs = list()

            for application in applications:
                job = job_cursor.find_one({"_id": application["job"]})

                user = user_cursor.find_one({"_id": application["applicant"]})

                pdf = pdf_cursor.find_one({"user": user["email"]}) if user else None
                if not pdf:
                    pdf = dict()

                if job and user:
                    applied_jobs.append(
                        {
                            "jobId": str(job["_id"]),
                            "applicationId": str(application["_id"]),
                            "applicantEmail": user["email"],
                            "fullName": user.get("fullName"),
                            "jobTitle": job["job_title"],
                            "company": job.get("company"),
                            "timeCreated": application["timeCreated"],
                            "status": application["status"],
                            "userResume": {
                                "filename": pdf.get("filename"),
                            },
                        }
                    )
            return {"jobs": applied_jobs}

    except Exception as e:
        return JSONResponse(content={"error": e}, status_code=501)


@JobRouter.post("/comment")
async def create_comment(
    create_comment: CreateComment, token_payload: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_document(token_payload=token_payload)
        cursor = get_cursor("ai", "comments")

        if user:
            cursor.insert_one(
                {
                    "application": ObjectId(create_comment.applicationId),
                    "user": user["_id"],
                    "text": create_comment.text,
                    "timeCreated": datetime.now(),
                }
            )

    except Exception as e:
        return JSONResponse(content={"error": e}, status_code=501)


@JobRouter.post("/comments")
async def get_comment(gather_comment: GatherComment):
    try:
        cursor = get_cursor("ai", "comments")
        user_cursor = get_cursor("ai", "users")

        comments = cursor.find({"application": ObjectId(gather_comment.applicationId)})
        comments = [comment for comment in comments]

        for comment in comments:
            user = user_cursor.find_one({"_id": comment["user"]})

            comment.pop("_id")

            if user:
                comment["application"] = str(comment["application"])
                comment["user"] = str(comment["user"])
                comment["userName"] = user.get("fullName")
                comment["userEmail"] = user["email"]

                print(comment)

        return {"comments": comments}

    except Exception as e:
        return JSONResponse(content={"error": e}, status_code=501)

# PDM
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime

from backend.utils import get_user_document, oauth2_scheme
from backend.mongo import get_cursor
from ragutils import query_by_job_id

ChatRouter = APIRouter()

LOG = logging.getLogger(__name__)

def fetch_resumes_by_job_id(job_id: str):
    client = MongoClient()
    db = client['pdfs']
    applications_collection = db['applications']
    resumes = []

    # Fetch applications linked to the job_id
    applications = applications_collection.find({"job": ObjectId(job_id)})
    for application in applications:
        # Assuming resumes are stored in a collection named 'resumes'
        resume = db.resumes.find_one({"_id": application['applicant']})
        if resume:
            resumes.append(resume)

    return resumes

@ChatRouter.post("/chat/{job_id}/query")
async def chat_query(job_id: str, question: str, job_title: str, job_desc: str, top_k: int = 3, token: str = Depends(oauth2_scheme)):
    # Assuming the user's authentication and authorization
    user = get_user_document(token_payload=token, trim_ids=True)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Call the rag_utils query function
        answer = query_by_job_id(question, job_id, job_title, job_desc, top_k)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

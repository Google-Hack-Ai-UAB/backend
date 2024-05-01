# PDM
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime

from backend.utils import oauth2_scheme
from backend.mongo import get_cursor

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

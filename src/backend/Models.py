# PDM
from pydantic import BaseModel


class ReadResume(BaseModel):
    user: str


class ApplyForJob(BaseModel):
    job_id: str


class CreateComment(BaseModel):
    text: str
    applicationId: str


class GatherComment(BaseModel):
    applicationId: str

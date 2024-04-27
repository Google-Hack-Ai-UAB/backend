# PDM
from pydantic import BaseModel


class ReadResume(BaseModel):
    user: str


class ApplyForJob(BaseModel):
    job_id: str

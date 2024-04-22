from pydantic import BaseModel


class ReadResume(BaseModel):
    user: str

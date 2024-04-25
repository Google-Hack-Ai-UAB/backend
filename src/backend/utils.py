import base64
import csv
import io
import tempfile
from typing import Optional

import bcrypt
import fitz
import jwt
import PyPDF2
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer
from gridfs import GridFS
from jwt import PyJWTError
from jwt import decode as jwt_decode
from pydantic import BaseModel

from backend.constants import ALGORITHM, CLIENT_ID, DOMAIN, SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_jwt_token(user: dict, db):
    user_collection = db["users"]
    found_user = user_collection.find_one({"email": user["email"]})

    to_encode = {"role": found_user["role"], "email": found_user["email"]}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(create_jwt_token)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("email")
        role: str = payload.get("role")  # Extract the "role" claim
        if username is None or role is None:
            raise credentials_exception
        token_data = {"email": username, "role": role}
    except jwt.PyJWTError:
        raise credentials_exception
    return token_data


def decode_role(current_user: dict = Depends(get_current_user)):
    return current_user.get("role")


def store_pdf(db, pdf, email):
    fs = GridFS(db, collection="pdfs")  # Use a custom collection for PDFs

    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(pdf)
            tmp.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return fs.put(open(tmp.name, "rb"), metadata={"user_email": email})


def binary_to_pdf(binary_data):
    pdf_data = base64.b64decode(binary_data)
    pdf_buffer = io.BytesIO(pdf_data)

    return pdf_buffer


async def import_csv(file: UploadFile = File(...)):
    json_data = []

    # Process the uploaded CSV file
    content = await file.read()
    content_str = content.decode("utf-8").split("\n")

    # Assuming the first row is the header
    headers = content_str[0].split(",")

    for line in content_str[1:]:
        if line:
            values = line.split(",")
            row = dict(zip(headers, values))
            json_data.append(row)

    return {"json_data": json_data}


def binary_to_text(pdf_binary_data):
    try:
        pdf_document = fitz.open(stream=pdf_binary_data, filetype="pdf")

        text = ""
        for page_number in range(pdf_document.page_count):
            page = pdf_document.load_page(page_number)
            text += page.get_text()

        return text

    except Exception as e:
        print(f"Error converting PDF to text: {e}")
        return None


def pdf_to_bytes(pdf_data):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
    pdf_writer = PyPDF2.PdfWriter()

    for page_num in range(pdf_reader.getNumPages()):
        pdf_writer.addPage(pdf_reader.getPage(page_num))

    pdf_output = io.BytesIO()
    pdf_writer.write(pdf_output)
    pdf_bytes = pdf_output.getvalue()

    return pdf_bytes


def decode_jwt(token: str) -> dict:
    try:
        decoded_token = jwt_decode(token, options={"verify_signature": False})
        return decoded_token
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


def get_job_listing_info():
    with open("allJobs.csv", "r") as f:
        reader = csv.reader(f)
        return [row for row in reader]

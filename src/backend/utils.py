# STL
import logging
from typing import Optional

# PDM
import requests
from jwt import PyJWTError
from jwt import decode as jwt_decode
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

# LOCAL
from backend.mongo import get_cursor
from backend.constants import DOMAIN

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

LOG = logging.getLogger(__name__)


def decode_jwt(token: str) -> dict:
    """Decode JWT tokens"""
    try:
        decoded_token = jwt_decode(token, options={"verify_signature": False})
        return decoded_token
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


def get_user_document(
    token_payload: str = Depends(oauth2_scheme), trim_ids=False
) -> Optional[dict]:
    """Get details about a user from an auth token."""
    try:
        response = requests.get(
            f"https://{DOMAIN}/userinfo",
            headers={"Authorization": f"Bearer {token_payload}"},
        )

        user_data = response.json()
        LOG.error(f"User Data: {user_data}")

        cursor = get_cursor("ai", "users")
        user = cursor.find_one({"email": user_data["email"]})

        if user and trim_ids:
            user.pop("_id")
            user.pop("userId")

        return user

    except Exception:
        LOG.warning("Requests being rate limited, try again.")
        return

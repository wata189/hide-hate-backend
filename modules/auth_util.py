from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import firebase_admin
from firebase_admin import auth, firestore
from dataclasses import dataclass

from modules import model, firestore_util

if (not len(firebase_admin._apps)):
  firebase_admin.initialize_app()

class JWTBearer(HTTPBearer):
  def __init__(self, auto_error: bool = True):
    super(JWTBearer, self).__init__(auto_error=auto_error)

  async def __call__(self, request: Request):
    credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
    if not credentials.scheme == "Bearer":
      raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
    if not self.verify_jwt(credentials.credentials):
      raise HTTPException(status_code=403, detail="Invalid token or expired token.")
    return credentials.credentials

  def verify_jwt(self, jwtoken: str) -> bool:
    isTokenValid: bool = False
    try:
      payload = auth.verify_id_token(jwtoken)
    except:
      payload = None
    if payload:
      isTokenValid = True

    return isTokenValid


@dataclass
class UserResponse:
  id: str
  email: str
  name: str

def get_authenticated_user(transaction: firestore.firestore.Transaction, authorization:str) -> UserResponse:
  if authorization:
    jwt = authorization.split(" ")[1]
    decoded_token = auth.verify_id_token(jwt)
    email = decoded_token["email"]
    user_collection:list[model.User] = firestore_util.select_firestore(transaction, "m_user", "email", "==", email)
    if len(user_collection) == 1:
      user_doc = user_collection[0]
      return {
        "id": user_doc["id"],
        "email": email,
        "name": user_doc["name"]
      }
    else:
      raise HTTPException(status_code=403, detail="User not found.")
  else:
    raise HTTPException(status_code=403, detail="Authorization header not found.")

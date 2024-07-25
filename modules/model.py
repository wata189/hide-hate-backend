from firebase_admin import firestore
from pydantic import BaseModel
from dataclasses import dataclass

from modules import firestore_util, auth_util


@dataclass
class Firestore_Dict:
  doc_id: str
  create_at: int
  create_user_id: str
  update_at: int
  update_user_id: str

@dataclass
class Post(Firestore_Dict):
  user_id: str
  content: str
  may_hate: bool

@dataclass
class User(Firestore_Dict):
  id: str
  name: str
  email: str
  hashed_password: str

@dataclass
class Timeline:
  post_doc_id: str
  user_id: str
  content: str
  may_hate: bool
  create_at: int
  name: str
  
def fetch_timeline(transaction: firestore.firestore.Transaction):
  posts:list[Post] = fetch_post(transaction)
  users:list[User] = fetch_user(transaction)

  timelines:list[Timeline] = []

  for post in posts:
    user = next(filter(lambda u: u["id"] == post["user_id"], users), None)
    timelines.append({
      "post_doc_id": post["doc_id"],
      "user_id": post["user_id"],
      "content": post["content"],
      "may_hate": post["may_hate"],
      "create_at": post["create_at"],
      "name": user["name"] if user else ""
    })

  return sorted(timelines, key=lambda t: t["create_at"], reverse=True)

def fetch_post(transaction: firestore.firestore.Transaction):
  posts:list[Post] = firestore_util.select_firestore(transaction, "t_post")
  return posts

def delete_user_auth_info(user: User):
  del user.hashed_password
  del user.email
  return user

def fetch_user(transaction: firestore.firestore.Transaction):
  users:list[User] = firestore_util.select_firestore(transaction, "m_user")
  
  return users


class PostParams(BaseModel):
  content: str
  accept_may_hate: bool
def create_post(transaction:firestore.firestore.Transaction, params:PostParams, may_hate:bool, authorization:str):
  user:auth_util.UserResponse = auth_util.get_authenticated_user(transaction, authorization)
  userId = user["id"]
  doc = {
    "user_id": userId,
    "content": params.content,
    "may_hate": may_hate,
    "create_user_id": userId,
    "update_user_id": userId
  }
  firestore_util.add_firestore(transaction, "t_post", doc)

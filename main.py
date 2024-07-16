import contextlib
from agraffe import Agraffe
from fastapi import FastAPI, Request
import os
import pickle
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore, storage
from typing import Callable, Union
from dataclasses import dataclass

##################################設定###############################################
@contextlib.asynccontextmanager
async def lifespan(app):
    yield {'message': 'hello'}

app = FastAPI(lifespan=lifespan)

# 環境変数読み込み
ENV = os.environ.get("ENV")
CLIENT_URL  = os.environ.get("CLIENT_URL")
# CORSの設定
RESPONSE_HEADERS = {
  "Access-Control-Allow-Origin": CLIENT_URL
}

if (not len(firebase_admin._apps)):
  firebase_admin.initialize_app()




##################################ルーティング###############################################
@app.get("/fetch")
def fetch():
  timelines:list[Timeline] = run_transaction([fetch_timeline])
  return {"timelines": timelines}


################################## Model ###############################################
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
  posts:list[Post] = select_firestore(transaction, "t_post")
  return posts

def delete_user_auth_info(user: User):
  del user.hashed_password
  del user.email
  return user

def fetch_user(transaction: firestore.firestore.Transaction):
  users:list[User] = select_firestore(transaction, "m_user")
  
  return users



############################################# DButil #################################################
db = firestore.client()

def run_transaction(funcs: list[Callable[[firestore.firestore.Transaction], any]]):
  """
  Firestore トランザクションをラップする関数
  """
  transaction = db.transaction()

  @firestore.transactional
  def tmp(transaction: firestore.firestore.Transaction):
    result = None
    for func in funcs:
      result = func(transaction)
    return result
  return tmp(transaction)


def doc_to_dict(doc:firestore.firestore.DocumentSnapshot):
  """
  Firestoreのドキュメントを dictに変換する
  """
  dict = doc.to_dict()
  dict["doc_id"] = doc.id # ドキュメントのid持たせとく
  # create_at, update_atはエポック秒に変換
  dict["create_at"] = int(round(dict["create_at"].timestamp()))
  dict["update_at"] = int(round(dict["update_at"].timestamp()))
  return dict
  

def select_firestore(transaction: firestore.firestore.Transaction, collection_path: str, field_path: Union[str, None] = None, op_string: Union[str, None] = None, value: Union[any, None] = None):
  """
  Firestoreの特定コレクションを読み出す
  """
  ref = db.collection(collection_path)
  if field_path is not None and op_string is not None and value is not None:
    ref = ref.where(field_path, op_string, value)

  docs = ref.get(transaction)
  
  results = list(map(doc_to_dict, docs))
  
  return results


def add_firestore(transaction: firestore.firestore.Transaction, collection_path: str, doc: dict, doc_id: str):
  # タイムスタンプだけ設定
  create_at = firestore.SERVER_TIMESTAMP
  doc["create_at"] = create_at
  doc["update_at"] = create_at

  new_document = db.collection(collection_path).document(doc_id)
  transaction.set(new_document, doc)
  print("insert " + doc_id)
  return new_document.id

def update_firestore(transaction: firestore.firestore.Transaction, collection_path: str, doc: dict, doc_id: str):
  # タイムスタンプだけ設定
  create_at = firestore.SERVER_TIMESTAMP
  doc["update_at"] = create_at

  new_document = db.collection(collection_path).document(doc_id)
  transaction.set(new_document, doc, merge=True)
  print("update " + doc_id)
  return new_document.id

@dataclass
class Bulk_Document:
  doc_id: str
  doc: dict

def add_bulk_firestore(transaction: firestore.firestore.Transaction, collection_path: str, bulk_documents: list[Bulk_Document]):
  for bulk_document in bulk_documents:
    add_firestore(transaction, collection_path, bulk_document.doc, bulk_document.doc_id)

def update_bulk_firestore(transaction: firestore.firestore.Transaction, collection_path: str, bulk_documents: list[Bulk_Document]):
  for bulk_document in bulk_documents:
    update_firestore(transaction, collection_path, bulk_document.doc, bulk_document.doc_id)

@dataclass
class Firestore_Dict:
  doc_id: str
  create_at: int
  create_user_id: str
  update_at: int
  update_user_id: str

############################################# Storage util #################################################
# 開発環境ではない場合はGCPに接続
if(ENV != "development"):
  STORAGE_BUCKET_NAME = os.environ.get("STORAGE_BUCKET_NAME")
  bucket = storage.bucket(STORAGE_BUCKET_NAME)
PATH_LOCAL_DATA = os.environ.get("PATH_LOCAL_DATA")

def open_file(file_name:str):
  """
  ファイルをCloud Storageから取得する

  Args:
      file_name (str): ファイル名

  Returns:
      Any: ローカルまたはCloud Storageから取得したファイル 
  """
  file = None
  # 開発環境の場合はローカルファイルから取り出し
  if ENV == "development":
    with open(os.path.join(PATH_LOCAL_DATA, file_name), mode='rb') as f:
      file = pickle.load(f)
  else:
    # GCPからファイル取得
    blob = bucket.blob(file_name)
    file = pickle.loads(blob.download_as_string())
  
  return file

entry_point = Agraffe.entry_point(app)
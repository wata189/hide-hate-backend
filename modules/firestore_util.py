import firebase_admin
from firebase_admin import firestore
from typing import Callable, Union
from dataclasses import dataclass

if (not len(firebase_admin._apps)):
  firebase_admin.initialize_app()
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


def add_firestore(transaction: firestore.firestore.Transaction, collection_path: str, doc: dict, doc_id: Union[str|None] = None):
  # タイムスタンプだけ設定
  create_at = firestore.SERVER_TIMESTAMP
  doc["create_at"] = create_at
  doc["update_at"] = create_at

  new_document = db.collection(collection_path).document(doc_id)
  transaction.set(new_document, doc)
  msg = "add" + doc_id if doc_id is not None else "add"
  print(msg)
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
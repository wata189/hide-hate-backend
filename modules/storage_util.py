import os
import firebase_admin
from firebase_admin import storage
import joblib

if (not len(firebase_admin._apps)):
  firebase_admin.initialize_app()

ENV = os.environ.get("ENV")
# 本番の場合はGCPに接続
if(ENV == "production"):
  STORAGE_BUCKET_NAME = os.environ.get("STORAGE_BUCKET_NAME")
  bucket = storage.bucket(STORAGE_BUCKET_NAME)
else:
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
      file = joblib.load(f)
  else:
    # GCPからファイル取得
    blob = bucket.blob(file_name)
    file = joblib.loads(blob.download_as_string())
  
  return file
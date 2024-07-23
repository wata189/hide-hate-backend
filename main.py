import contextlib
from agraffe import Agraffe
from fastapi import Depends, FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
import os
from pydantic import BaseModel

from modules import ai_util, firestore_util, auth_util, model

##################################設定###############################################
@contextlib.asynccontextmanager
async def lifespan(app):
    yield {'message': 'hello'}

app = FastAPI(lifespan=lifespan)

# 環境変数読み込み
ENV = os.environ.get("ENV")
CLIENT_URL  = os.environ.get("CLIENT_URL")
# CORSの設定
app.add_middleware(
  CORSMiddleware,
  allow_origins=[CLIENT_URL],
  allow_credentials=False,
  allow_methods=["*"],
  allow_headers=["*"],
)

##################################ルーティング###############################################
@app.get("/fetch")
def fetch():
  timelines:list[model.Timeline] = firestore_util.run_transaction([model.fetch_timeline])
  return {"timelines": timelines}


@app.get("/user/get", dependencies=[Depends(auth_util.JWTBearer())])
def get_user(Authorization:str = Header()):
  user: auth_util.UserResponse = firestore_util.run_transaction([lambda t: auth_util.get_authenticated_user(t, Authorization)])
  return {
    "user": user
  }

class CreateParams(BaseModel):
  content: str
  accept_may_hate: bool
@app.post("/create", dependencies=[Depends(auth_util.JWTBearer())])
def create(params: CreateParams, Authorization:str = Header()):
  # ヘイトチェック
  may_hate:bool = ai_util.may_hate_by_ai(params.content)
  timelines:list[model.Timeline] = []

  # ヘイト判定受けたことを確認しているか、aiの結果がヘイト判定受けていない場合は投稿
  if params.accept_may_hate or not may_hate:
    timelines = firestore_util.run_transaction([lambda t: model.create_post(t, params, may_hate, Authorization)])
    # 更新後のタイムライン表示
    timelines:list[model.Timeline] = firestore_util.run_transaction([model.fetch_timeline])

  return {"may_hate": may_hate, "timelines": timelines}

entry_point = Agraffe.entry_point(app)
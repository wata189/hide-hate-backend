from typing import Union
import pandas
from janome.tokenizer import Tokenizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
import joblib
from modules import ai_util

import time
import os
TEST_SIZE = 0.2

explanatory_col = "text"
objectiv_col = "label"
PATH_DATA = "data"

#トレーニングデータと検証用のテストデータに分割
def split_data_frame(df:pandas.DataFrame, objectiv_col:str):
  df_train, df_val =train_test_split(df, test_size=TEST_SIZE, random_state=42)
  train_y = df_train[objectiv_col]
  train_x = df_train.drop(objectiv_col, axis=1)

  val_y = df_val[objectiv_col]
  val_x = df_val.drop(objectiv_col, axis=1)
  return [train_x, train_y, val_x, val_y]

def clean_text(text):
  return text.replace(' ', '').replace('　', '').replace('__BR__', '\n').replace('\xa0', '').replace('\r', '').lstrip('\n')

# データ読み込みと前処理
df_hate_train = pandas.read_csv(PATH_DATA + "/train.csv", index_col=0)
df_hate_train.drop("source", axis=1)
df_hate_test = pandas.read_csv(PATH_DATA + "/test.csv", index_col=0)
df_hate_test.drop("source", axis=1)
df_hate_train[explanatory_col] = df_hate_train[explanatory_col].apply(clean_text)
df_hate_test[explanatory_col] = df_hate_test[explanatory_col].apply(clean_text)
df_tweet = pandas.read_csv(PATH_DATA + "/tweet.csv", index_col=0)
df_tweet[explanatory_col] = df_tweet[explanatory_col].apply(clean_text)

# トークナイザーの設定
all_texts = list(df_hate_train["text"])
all_texts.extend(list(df_hate_test["text"]))

# ベクトライザーの設定
vectorizer = CountVectorizer(tokenizer=ai_util.tokenize, token_pattern=None)
vectorizer.fit(all_texts)

# いったんベクトライザー保存して再度読み込み
tmp = str(round(time.time()))
vectorizer_file_name = tmp + "_vectorizer.pkl"
with open(os.path.join("model", vectorizer_file_name), mode='wb') as f:
  joblib.dump(vectorizer, f, protocol=2)

loaded_vectorizer = joblib.load(os.path.join("model", vectorizer_file_name))


# テストデータを分割
train_x, train_y, val_x, val_y = split_data_frame(df_hate_train, objectiv_col)

# テキストをベクトル化
train_vectors = loaded_vectorizer.transform(train_x[explanatory_col])
val_vectors = loaded_vectorizer.transform(val_x[explanatory_col])
tweet_vectors = loaded_vectorizer.transform(df_tweet[explanatory_col])

#モデル作成
model = MLPClassifier(hidden_layer_sizes=(16,), random_state=42)
model.fit(train_vectors, train_y)

#train.csvのデータとtweet.csvのデータで正解率・AUC見る
print("-----------------------train.csvデータ----------------")
print("正解率:" + str(accuracy_score(val_y, model.predict(val_vectors))))
print("AUC:" + str(roc_auc_score(val_y, model.predict_proba(val_vectors)[:, 1])))

print("-----------------------tweet.csvデータ----------------")
print("正解率:" + str(accuracy_score(df_tweet[objectiv_col], model.predict(tweet_vectors))))
print("AUC:" + str(roc_auc_score(df_tweet[objectiv_col], model.predict_proba(tweet_vectors)[:, 1])))

# モデルを保存
file_name = tmp + "_nn_model.pkl"
with open(os.path.join("model", file_name), mode='wb') as f:
  joblib.dump(model, f, protocol=2)
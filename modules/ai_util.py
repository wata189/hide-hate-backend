

from sklearn.neural_network import MLPClassifier
from sklearn.feature_extraction.text import CountVectorizer
from modules import storage_util
from janome.tokenizer import Tokenizer

tokenizer = Tokenizer()
def tokenize(text:str):
  return tokenizer.tokenize(text, wakati=True)

MODEL_FILE_NAME = "nn_model.pkl"
VECTORIZER_FILE_NAME = "vectorizer.pkl"
def may_hate_by_ai(content:str):
  nn_model:MLPClassifier = storage_util.open_file(MODEL_FILE_NAME)
  vectorizer:CountVectorizer = storage_util.open_file(VECTORIZER_FILE_NAME)

  vectors = vectorizer.transform([content])

  result = int(nn_model.predict(vectors)[0])
  return result == 1
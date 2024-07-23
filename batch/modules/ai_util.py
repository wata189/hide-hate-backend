

from janome.tokenizer import Tokenizer
tokenizer = Tokenizer()
def tokenize(text:str):
  return tokenizer.tokenize(text, wakati=True)
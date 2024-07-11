import flask
from flask import Request, request
import werkzeug.datastructures


app = flask.Flask(__name__)

## ルーティング
@app.route("/test", methods=["GET"])
def test():
  return "hello test!"


@app.route("/fetch", methods=['POST'])
def fetch():
  return "hello " + request.path


def main(request: Request):
  with app.app_context():
    headers = werkzeug.datastructures.Headers()
    for key, value in request.headers.items():
      headers.add(key, value)
    with app.test_request_context(method=request.method, base_url=request.base_url, path=request.path, query_string=request.query_string, headers=headers, data=request.data):
      try:
        rv = app.preprocess_request()
        if rv is None:
          rv = app.dispatch_request()
      except Exception as e:
        rv = app.handle_user_exception(e)
      response = app.make_response(rv)
      return app.process_response(response)

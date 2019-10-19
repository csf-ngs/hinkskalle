from Hinkskalle import app
from flask import jsonify, make_response

def create_error_object(code, msg):
  return [
    { 'title': 'Fail!', 'detail': msg, 'code': code }
  ]

@app.errorhandler(404)
def not_found(error):
  return make_response(jsonify(status='error', errors=create_error_object(404, 'Not found.')), 404)

@app.errorhandler(500)
def internal_error(error):
  return make_response(jsonify(status='error', errors=create_error_object(500, str(error))), 500)

@app.errorhandler(403)
def forbidden_error(error):
  return make_response(jsonify(status="error", errors=create_error_object(403, str(error))), 403)

@app.after_request
def add_header(r):
  r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
  r.headers["Pragma"] = "no-cache"
  r.headers["Expires"] = "0"
  r.headers['Cache-Control'] = 'public, max-age=0'
  return r
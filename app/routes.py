from app import parser
import json
from flask import render_template, request, Response
from sqlalchemy import exc

from app import app

@app.route('/')
@app.route('/index')
def index():
    return render_template('resultTable.html')

@app.route('/_raw_data/', methods=['GET'])
def getcalls_finish():
    date_start = request.args.get("date_start")
    date_end = request.args.get("date_end")

    try:
        calls_data_raw = parser.get_call_data_final(date_start=date_start, date_end=date_end)
        answer = {"result": calls_data_raw}
    except exc.OperationalError as e:
        answer = {"error": str(e.orig.args[1])}

    json_response=json.dumps(answer, default=str)
    response=Response(json_response,content_type='application/json; charset=utf-8')
    response.headers.add('content-length',len(json_response))
    response.status_code=200

    return response
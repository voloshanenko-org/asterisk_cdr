from app import parser
import json
import os
from flask import render_template, request, Response, url_for
from sqlalchemy import exc
from app import app

@app.route('/')
@app.route('/index')
def index():
    return render_template('resultTable.html')


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename is not None:
            path = os.path.join(app.root_path, endpoint, filename)
            values['ts'] = int(os.stat(path).st_mtime)
    return url_for(endpoint, **values)


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
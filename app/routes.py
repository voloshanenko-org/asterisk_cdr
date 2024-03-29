from app import parser, aster
from json import dumps
import os
from datetime import datetime
from werkzeug.urls import url_parse
from flask import render_template, request, Response, url_for, redirect, flash
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import exc
from app import app


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


@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('resultTable.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = checked = 'rememberme_check' in request.form
        if username and password:
            try:
                user, login_passed = parser.check_user_credentials(username, password)
            except ConnectionError:
                user, login_passed = None, False
            if not login_passed:
                flash('Invalid username or password', 'error')
                return redirect(url_for('login'))
            login_user(user, remember=remember_me)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
        else:
            flash('All fileds required!', 'error')
    return render_template('login.html', title='Sign In')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/_raw_data/', methods=['GET'])
@login_required
def get_calldata_response():
    date_start = request.args.get("date_start")
    date_end = request.args.get("date_end")

    try:
        date_start_obj = datetime.strptime(date_start, '%Y-%m-%d %H:%M:%S')
        date_end_obj = datetime.strptime(date_end, '%Y-%m-%d %H:%M:%S')
        if date_start_obj > date_end_obj:
            raise ValueError("End date/time can't be lower than start date!")
        try:
            calls_data_raw = parser.calldata_json(date_start=date_start, date_end=date_end)
            answer = {"result": calls_data_raw}
        except exc.OperationalError as e:
            answer = {"error": str(e.orig.args[1])}
    except ValueError as e:
        answer = {"error": str(e.args[0])}

    json_response=dumps(answer, default=str)
    response=Response(json_response,content_type='application/json; charset=utf-8')
    response.headers.add('content-length',len(json_response))
    response.status_code=200

    return response


@app.route('/_init_call/', methods=['GET'])
@login_required
def init_call_response():
    from_sip_user = current_user.id
    to_sip_number = request.args.get("dstnum")

    if not from_sip_user or not to_sip_number:
        call_init_status = '{ "error": "PBX_REQUEST_INVALID" }'
    else:
        call_init_status = aster.run_call(from_sip_user, to_sip_number)

    response=Response(call_init_status,content_type='application/json; charset=utf-8')
    response.headers.add('content-length',len(call_init_status))
    response.status_code=200

    return response


@app.route('/_sip_status/', methods=['GET'])
@login_required
def sip_status_response():
    sip_user = current_user.id
    webrtc_user = "99" + sip_user
    final_status = ""
    sip_status = aster.get_sip_status(sip_user)
    webrtc_status = aster.get_sip_status(webrtc_user)

    if "error" in sip_status and "status" in webrtc_status:
        final_status = webrtc_status
    elif (
        "error" in webrtc_status
        and "status" in sip_status
        or "error" in sip_status
        and "error" in webrtc_status
    ):
        final_status = sip_status
    response=Response(final_status,content_type='application/json; charset=utf-8')
    response.headers.add('content-length',len(final_status))
    response.status_code=200

    return response


@app.route('/_all_sip_status/', methods=['GET'])
@login_required
def all_sip_status_response():
    all_sip_status = aster.get_all_sip_status()

    json_response=dumps(all_sip_status, default=str)
    response=Response(json_response,content_type='application/json; charset=utf-8')
    response.headers.add('content-length',len(json_response))
    response.status_code=200

    return response


@app.route('/_record_data/', methods=['GET'])
@login_required
def get_record_file():
    record_hash = request.args.get("record_file_id")
    return ""
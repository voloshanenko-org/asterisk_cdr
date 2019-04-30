from app.models import CallsLog, CelLog, User
from sqlalchemy import and_, not_, or_
from itertools import groupby
from operator import itemgetter
from sqlalchemy import exc
import json
import re


def check_user_credentials(username, password):
    user = User.query\
        .filter(User.keyword == "secret")\
        .filter(User.id == username)\
        .first()

    if user is None or not user.data == password:
        return None, False
    else:
        return user, True


def raw_calldata(date_start, date_end):
    try:
        cels = CelLog.query \
        .filter(and_(CelLog.eventtime > date_start, CelLog.eventtime < date_end)) \
        .filter(not_(CelLog.channame.like("%PJSIP/anonymous%"))) \
        .filter(or_(
                    and_(CelLog.eventtype == "BRIDGE_ENTER", CelLog.context.like("macro-dial%"), not_(CelLog.appname == "AppDial")),
                    and_(CelLog.eventtype == "CHAN_START", not_(CelLog.context == "from-queue"), not_(CelLog.exten == "s")),
                    and_(CelLog.eventtype == "HANGUP", not_(CelLog.cid_dnid == "")),
                    and_(CelLog.eventtype == "APP_START", CelLog.appname == "MixMonitor")
        )) \
        .order_by(CelLog.linkedid, CelLog.id).all()
    except exc.OperationalError as e:
        raise

    grouped_calls_data = {k:list(v) for k,v in groupby(cels,key=itemgetter("linkedid"))}
    return grouped_calls_data


def calldata_json(date_start, date_end):

    try:
        grouped_cels_data = raw_calldata(date_start, date_end)
        final_data = []

        for linked_id, linked_events in grouped_cels_data.items():

            call_data = {}
            records = []
            call_start = None
            call_end = None
            talk_start = None

            for event in linked_events:

                # if Start of the call
                if event["eventtype"] == "CHAN_START":
                    # Set event linkedID
                    call_data.setdefault("linkedid",event["linkedid"])
                    call_data.setdefault("calldate",event["eventtime"])
                    # Set call_start data
                    call_start = event["eventtime"]
                    #Set incoming or outgoing call
                    if event["context"] == "from-pstn":
                        call_data.setdefault("direction", "Incoming")
                    elif event["context"] == "from-internal":
                        call_data.setdefault("direction", "Outgoing")
                        # Set src/dst for outgoing call
                        call_data.setdefault("src", event["cid_num"])
                        call_data.setdefault("dst", event["exten"])
                    else:
                        print("Unknown call context: " + event["context"])
                        raise ValueError(event["context"])
                elif event["eventtype"] == "APP_START":
                    records.append(event["appdata"].split(",")[0])
                elif event["eventtype"] == "BRIDGE_ENTER":
                    talk_start = event["eventtime"]
                    call_data.setdefault("src", event["cid_num"])
                    # if incoming call answered - set by whom below
                    if event["context"] == "macro-dial-one":
                        dst_extension_search = re.search('PJSIP/(.*)/sip:.*', event["appdata"], re.IGNORECASE)
                        if dst_extension_search:
                            call_data.setdefault("dst", dst_extension_search.group(1))
                # If end of the call
                elif event["eventtype"] == "HANGUP":
                    # Set call_end data
                    call_end = event["eventtime"]
                    call_extra_data = json.loads(event["extra"])
                    call_status = call_extra_data["dialstatus"]
                    if event["context"] == "ext-queues":
                        # Set src/dst for incoming missed call
                        call_data.setdefault("src", event["cid_num"])
                    elif event["context"] == "ext-local":
                        call_data["direction"] = "Internal"
                    if call_status == "ANSWER":
                        table_call_status = "ANSWERED"
                    elif call_status == "CONGESTION":
                        table_call_status = "MISSED"
                    elif call_status in ["NOANSWER", "CANCEL"]:
                        table_call_status = "NO ANSWER"
                    elif not call_status:
                        table_call_status = "MISSED"
                    else:
                        table_call_status = call_status

                    call_data.setdefault("disposition", table_call_status)

                else:
                    print("Unknown call eventtype: " + event["eventtype"])
                    raise ValueError(event["eventtype"])

            if call_data:
                if talk_start:
                    call_data.setdefault("waiting_duration",(talk_start - call_start).seconds)
                    call_data.setdefault("talking_duration",(call_end - talk_start).seconds)
                    record = [rec for rec in records if "-" + call_data['dst'] + "-" in rec]
                    if record:
                        call_data["record_file"] = record[0]
                else:
                    call_data.setdefault("waiting_duration",(call_end - call_start).seconds)

                final_data.append(call_data)

        incoming_missed_calls=list(filter(lambda d: d['disposition'] == "MISSED" and d['direction'] == "Incoming" , final_data))
        outcoming_calls=list(filter(lambda d: d['direction'] != "Incoming" , final_data))

        #Find if missed call was recalled
        for idx, call in enumerate(final_data):
            if call['direction'] == "Incoming" and call["disposition"] == "MISSED":
                callback = list(filter(lambda d: d['dst'] in call['src'] and d['calldate'] > call['calldate'], outcoming_calls))
                if callback:
                    final_data[idx]["callback"] = {
                        "calldate": callback[0]['calldate'],
                        "src": callback[0]['src'],
                        "before_call": (callback[0]['calldate'] - call['calldate']).total_seconds()
                    }
            elif call['direction'] == "Outgoing":
                callback = list(filter(lambda d: call['dst'] in d['src'] and d['calldate'] < call['calldate'], incoming_missed_calls))
                if callback:
                    final_data[idx]["missed"] = {
                        "calldate": callback[0]['calldate'],
                        "src": callback[0]['src'],
                        "before_call": (call['calldate']-callback[0]['calldate']).total_seconds()
                    }

    except exc.OperationalError as e:
        raise

    return final_data
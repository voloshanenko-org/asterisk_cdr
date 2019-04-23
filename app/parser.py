from app.models import CallsLog
from sqlalchemy import and_, not_
from itertools import groupby
from operator import itemgetter
from sqlalchemy import exc
import re


def get_raw_call_data(date_start, date_end):
    calls = CallsLog.query\
        .filter(CallsLog.calldate > date_start, CallsLog.calldate < date_end) \
        .filter(not_(and_(CallsLog.dst == "s" ,CallsLog.lastapp == "Congestion"))) \
        .filter(not_(and_(CallsLog.lastapp == "Queue", CallsLog.disposition == "FAILED", CallsLog.billsec == 0, CallsLog.duration == 0))) \
        .order_by(CallsLog.calldate, CallsLog.uniqueid).all()
    return calls


def get_call_data_grouped(date_start, date_end):

    try:
        raw_calls_data = get_raw_call_data(date_start, date_end)
        grouped_calls_data = {k:list(v) for k,v in groupby(raw_calls_data,key=itemgetter("linkedid"))}
    except exc.OperationalError as e:
        raise

    return grouped_calls_data


def get_call_data_final(date_start, date_end):

    try:
        grouped_calls_data = get_call_data_grouped(date_start, date_end)
        final_data = []

        for v in grouped_calls_data:

            answered_call_data = [d for d in grouped_calls_data[v] if d["disposition"] == "ANSWERED"]
            not_answered_call_data = [d for d in grouped_calls_data[v] if d["disposition"] != "ANSWERED"]

            call_data = {}

            for call in answered_call_data:
                # Incoming call
                if call["dcontext"] in ['ext-local', 'ext-queues']:
                    if re.match(r"9[0-9][1-9]", call["src"]):
                        continue

                    call_data.setdefault("calldate", call["calldate"])
                    call_data.setdefault("direction", "in")
                    call_data.setdefault("src", call["src"])
                    call_data.setdefault("disposition", call["disposition"])
                    call_data.setdefault("talking_duration", call["billsec"])
                    call_data.setdefault("waiting_duration", call["duration"] - call["billsec"])
                    call_data.setdefault("linkedid", call["linkedid"])

                    if call["calldate"] < call_data["calldate"]:
                        call_data["calldate"] = call["calldate"]

                    if call["dcontext"] == "ext-local":
                        call_data.setdefault("dst", call["dst"])
                        call_data["talking_duration"] = call["billsec"]
                        call_data["waiting_duration"] = call["duration"] - call["billsec"]

                # Outgoing call
                elif call["dcontext"] in ['from-internal']:
                    call_data.setdefault("calldate", call["calldate"])
                    call_data["direction"] = "out"
                    call_data.setdefault("src", call["cnum"])
                    call_data.setdefault("dst", call["dst"])
                    call_data.setdefault("disposition", call["disposition"])
                    call_data.setdefault("talking_duration", call["billsec"])
                    call_data.setdefault("waiting_duration", call["duration"] - call["billsec"])
                    call_data.setdefault("linkedid", call["linkedid"])
                else:
                    raise call
                    exit(1)

            if not call_data:
                for call in not_answered_call_data:
                    # Incoming call
                    if call["dcontext"] in ['ext-local', 'ext-queues']:
                        call_data.setdefault("calldate", call["calldate"])
                        call_data.setdefault("direction", "in")
                        call_data.setdefault("src", call["src"])
                        if (re.match(r"9[0-9][1-9]", call["src"]) and re.match(r"9[0-9][1-9]", call["dst"])):
                            call_data.setdefault("dst", call["dst"])
                        call_data.setdefault("disposition", "NO ANSWER")
                        call_data.setdefault("talking_duration", 0)
                        call_data.setdefault("waiting_duration", call["duration"] - call["billsec"])
                        call_data.setdefault("linkedid", call["linkedid"])

                        if call["calldate"] < call_data["calldate"]:
                            call_data["calldate"] = call["calldate"]

                        if call["duration"] - call["billsec"] > call_data["waiting_duration"]:
                            call_data["waiting_duration"] = call["duration"] - call["billsec"]

                    # Outgoing call
                    elif call["dcontext"] in ['from-internal']:
                        call_data.setdefault("calldate", call["calldate"])
                        call_data["direction"] = "out"
                        call_data.setdefault("src", call["cnum"])
                        call_data.setdefault("dst", call["dst"])
                        if call["disposition"] == "FAILED":
                            call_data.setdefault("disposition", "NO ANSWER")
                        else:
                            call_data.setdefault("disposition", call["disposition"])
                        call_data.setdefault("disposition", call["disposition"])
                        call_data.setdefault("talking_duration", 0)
                        call_data.setdefault("waiting_duration", call["duration"] - call["billsec"])
                        call_data.setdefault("linkedid", call["linkedid"])
                    else:
                        raise call
                        exit(1)

            if call_data:
                final_data.append(call_data)

        incoming_missed_calls=list(filter(lambda d: d['disposition'] == "NO ANSWER" and d['direction'] == "in" , final_data))
        outcoming_calls=list(filter(lambda d: d['direction'] == "out" , final_data))

        #Find if missed call was recalled
        for idx, call in enumerate(final_data):
            if call['direction'] == "in" and call["disposition"] == "NO ANSWER":
                callback = list(filter(lambda d: d['dst'] in call['src'] and d['calldate'] > call['calldate'], outcoming_calls))
                if callback:
                    final_data[idx]["callback"] = {
                        "calldate": callback[0]['calldate'],
                        "src": callback[0]['src'],
                        "before_call": (callback[0]['calldate'] - call['calldate']).total_seconds()
                    }
            elif call['direction'] == "out":
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
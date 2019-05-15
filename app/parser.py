from app.models import CelLog, User
from sqlalchemy import and_, not_, or_
from itertools import groupby
from operator import itemgetter
from sqlalchemy import exc
import json
import re
import timeout_decorator
import time
from app import app
from sqlalchemy.engine.default import DefaultDialect
from sqlalchemy.sql.sqltypes import String, DateTime, NullType


class StringLiteral(String):
    """Teach SA how to literalize various things."""
    def literal_processor(self, dialect):
        super_processor = super(StringLiteral, self).literal_processor(dialect)

        def process(value):
            if isinstance(value, int):
                return str(value)
            if not isinstance(value, str):
                value = str(value)
            result = super_processor(value)
            if isinstance(result, bytes):
                result = result.decode(dialect.encoding)
            return result
        return process


class LiteralDialect(DefaultDialect):
    colspecs = {
        # prevent various encoding explosions
        String: StringLiteral,
        # teach SA about how to literalize a datetime
        DateTime: StringLiteral,
        # don't format py2 long integers to NULL
        NullType: StringLiteral,
    }


# Limit time for connection Error
@timeout_decorator.timeout(3, use_signals=False, timeout_exception=ConnectionError)
def check_user_credentials(username, password):
    try:
        user = User.query\
            .filter(User.keyword == "secret")\
            .filter(User.id == username)\
            .first()
    except exc.OperationalError as e:
        return None, False

    if user is None or not user.data == password:
        return None, False
    else:
        return user, True


def raw_calldata(date_start, date_end):
    try:
        DEBUG = app.config["FLASK_DEBUG"]

        if DEBUG:
            start_time = time.time()

        # Get uniq linkedid for calls
        linkedid_query = CelLog.query \
            .with_hint(CelLog,"FORCE INDEX (eventtime)") \
            .with_entities(CelLog.linkedid) \
            .filter(CelLog.eventtime.between(date_start, date_end)) \
            .filter(not_(CelLog.channame.like("%PJSIP/anonymous%"))) \
            .distinct(CelLog.linkedid) \
            .order_by(CelLog.linkedid, CelLog.id)

        linkedid_data = linkedid_query.all()

        linkedid_data_filtered = []
        for l in linkedid_data:
            linkedid_data_filtered.append(l.linkedid.replace("'", ""))

        if DEBUG == "1":
            statement = linkedid_query.statement
            raw_text_sql=statement.compile(
                dialect=LiteralDialect(),
                compile_kwargs={'literal_binds': True},
            ).string
            #print("LinkedID SQL: " + raw_text_sql.replace("\n", ""))
            print("--- SQL (Get Uniq LinkedID for calls) execution time %s seconds ---" % (time.time() - start_time))
            start_time = time.time()

        # Retrieve all call data based on linkedid_data.
        # We don't want to miss call data for call which start at date range but finished later or finished at date range but started before.
        cels_query = CelLog.query \
        .filter(and_(CelLog.linkedid.in_(linkedid_data_filtered))) \
        .filter(not_(CelLog.channame.like("%PJSIP/anonymous%"))) \
        .filter(or_(
                    and_(CelLog.eventtype == "BRIDGE_ENTER", CelLog.context.like("macro-dial%"), not_(CelLog.appname == "AppDial")),
                    and_(CelLog.eventtype == "CHAN_START", not_(CelLog.context == "from-queue"), not_(CelLog.context == "from-pstn"), not_(CelLog.exten == "s")),
                    and_(CelLog.eventtype == "CHAN_START", CelLog.context == "from-internal", CelLog.exten == "s"),
                    and_(CelLog.eventtype == "CHAN_START", CelLog.context == "from-pstn"),
                    and_(CelLog.eventtype == "APP_START", CelLog.appname == "MixMonitor"),
                    CelLog.eventtype == "ANSWER",
                    and_(CelLog.eventtype == "HANGUP", not_(CelLog.cid_dnid == "")),
                    and_(CelLog.eventtype == "HANGUP", CelLog.context == "from-internal", not_(CelLog.cid_num == CelLog.exten))
        )) \
        .order_by(CelLog.linkedid, CelLog.id)
        cels = cels_query.all()

        if DEBUG == "1":
            statement = cels_query.statement
            raw_text_sql=statement.compile(
                dialect=LiteralDialect(),
                compile_kwargs={'literal_binds': True},
            ).string
            #print("Calls data SQL: " + raw_text_sql.replace("\n", ""))

            print("--- SQL (Get calls data based on LinkedID) execution time %s seconds ---" % (time.time() - start_time))

    except exc.OperationalError as e:
        raise

    if DEBUG:
        start_time = time.time()

    grouped_calls_data = {k:list(v) for k,v in groupby(cels,key=itemgetter("linkedid"))}

    if DEBUG:
        print("--- Data grouping execution time %s seconds ---" % (time.time() - start_time))

    return grouped_calls_data


def calldata_json(date_start, date_end):

    try:
        grouped_cels_data = raw_calldata(date_start, date_end)

        DEBUG = app.config["FLASK_DEBUG"]
        if DEBUG:
            start_time = time.time()

        final_data = []
        for linked_id, linked_events in grouped_cels_data.items():

            call_data = {}
            records = []
            call_start = None
            call_end = None
            talk_start = None

            temp_start_date = None
            temp_num = None
            temp_dst_num = None

            # Set event linkedID
            call_data.setdefault("linkedid",linked_id)

            for event in linked_events:

                # if Start of the call
                if event["eventtype"] == "CHAN_START":
                    if event["context"] == "from-internal" and event["exten"] == "s":
                        if not temp_start_date:
                            temp_start_date = event["eventtime"]
                    else:
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
                            print("ValueError.\nLinkedID:" + str(call_data["linkedid"]) + ", Unknown call context: " + event["context"])
                            raise ValueError("ValueError. LinkedID:" + str(call_data["linkedid"]) + ", Unknown call context: " + event["context"])
                elif event["eventtype"] == "APP_START":
                    records.append(event["appdata"].split(",")[0])
                    if not temp_num:
                        temp_num = event["cid_num"]
                    if not temp_start_date:
                        temp_start_date = event["eventtime"]
                    dst_temp_extension_search = re.search('.*/out-([0-9]+)-.*', event["appdata"], re.IGNORECASE)
                    if dst_temp_extension_search and not temp_dst_num:
                        temp_dst_num = dst_temp_extension_search.group(1)
                elif event["eventtype"] == "ANSWER":
                    if not temp_start_date:
                        temp_start_date = event["eventtime"]
                    if not temp_num:
                        temp_num = event["cid_num"]
                    dst_extension_search = re.search('Call_to_(.*)', event["cid_num"], re.IGNORECASE)
                    if dst_extension_search and not temp_dst_num:
                        temp_dst_num = dst_extension_search.group(1)
                elif event["eventtype"] == "BRIDGE_ENTER":
                    talk_start = event["eventtime"]
                    src_extension_search = re.search('Call_to_(.*)', event["cid_num"], re.IGNORECASE)
                    if not src_extension_search:
                        call_data.setdefault("src", event["cid_num"])
                        # if incoming call answered - set by whom below
                        if event["context"] == "macro-dial-one":
                            dst_extension_search = re.search('PJSIP/(.*)/sip:.*', event["appdata"], re.IGNORECASE)
                            if dst_extension_search:
                                call_data.setdefault("dst", dst_extension_search.group(1))
                # If end of the call
                elif event["eventtype"] == "HANGUP":
                    # Set call_end data
                    if event["appdata"] == "(Outgoing Line)" and not "src" in call_data:
                        call_extra_data = json.loads(event["extra"])
                        src_extension_search = re.search('PJSIP/(.*)-.*', call_extra_data["hangupsource"], re.IGNORECASE)
                        if src_extension_search:
                            additonal_src_extension_search = re.search('PJSIP/(.*)-.*', event["channame"], re.IGNORECASE)
                            if additonal_src_extension_search and additonal_src_extension_search != src_extension_search.group(1):
                                call_data.setdefault("src", additonal_src_extension_search.group(1))
                            else:
                                call_data.setdefault("src", src_extension_search.group(1))

                        dst_extension_search = re.search('Call_to_(.*)', event["cid_num"], re.IGNORECASE)
                        if dst_extension_search and not temp_dst_num:
                            temp_dst_num = dst_extension_search.group(1)
                        call_data["direction"] = "Outgoing"

                        call_end = event["eventtime"]
                        call_extra_data = json.loads(event["extra"])
                        call_status = call_extra_data["dialstatus"]
                    else:
                        if event["context"] == "ext-queues":
                            # Set src/dst for incoming missed call
                            call_data.setdefault("src", event["cid_num"])
                        elif event["context"] == "ext-local":
                            call_data["direction"] = "Internal"

                        call_end = event["eventtime"]
                        call_extra_data = json.loads(event["extra"])
                        call_status = call_extra_data["dialstatus"]
                else:
                    print("ValueError.\nLinkedID:" + str(call_data["linkedid"]) + ", Unknown call eventtype: " + event["eventtype"])
                    raise ValueError("ValueError. LinkedID:" + str(call_data["linkedid"]) + ", Unknown call eventtype: " + event["eventtype"])

            if call_data:
                table_call_status = None
                if call_status == "ANSWER":
                    table_call_status = "ANSWERED"
                elif call_status in ["CONGESTION","NOANSWER", "CANCEL", ""]:
                    if call_data["direction"] == "Incoming":
                        table_call_status = "MISSED"
                    elif call_data["direction"] == "Outgoing":
                        table_call_status = "NO ANSWER"
                else:
                    table_call_status = call_status
                call_data.setdefault("disposition", table_call_status)

                if not "dst" in call_data and call_data["direction"] == "Outgoing" and temp_dst_num:
                    if "src" in call_data:
                        call_data["dst"] = temp_dst_num
                    else:
                        continue

                if not call_start:
                    if "src" in call_data or "dst" in call_data:
                        if call_data["direction"] == "Outgoing" and temp_start_date:
                            call_data.setdefault("calldate", temp_start_date)
                            call_start = temp_start_date
                        else:
                            print("ValueError.\nLinkedID:" + str(call_data["linkedid"]) + ", Start: " + str(call_start))
                            raise ValueError("ValueError. LinkedID:" + str(call_data["linkedid"]) + ", Start: " + str(call_start))
                    else:
                        continue

                if call_end:
                    if talk_start:
                        call_data.setdefault("waiting_duration",(talk_start - call_start).seconds)
                        call_data.setdefault("talking_duration",(call_end - talk_start).seconds)
                        record = [rec for rec in records if "-" + call_data['dst'] + "-" in rec]
                        if record:
                            call_data["record_file"] = record[0]
                    else:
                        call_data.setdefault("waiting_duration",(call_end - call_start).seconds)
                else:
                    # Call still active. Set status to "Incall"
                    call_data.setdefault("disposition", "Incall")
                    call_data.setdefault("src", temp_num)

                final_data.append(call_data)

        if DEBUG:
            print("--- Initial data parsing execution time %s seconds ---" % (time.time() - start_time))
            start_time = time.time()

        # Replace +38 prefix if exist in src num for incoming calls
        for idx, call in enumerate(final_data):
            if call['direction'] == "Incoming":
                src_tel = re.search('38(.*)', call["src"], re.IGNORECASE)
                if src_tel:
                    final_data[idx]["src"] = src_tel.group(1)

        outcoming_calls=list(filter(lambda d: d['direction'] != "Incoming" and d['disposition'] == "ANSWERED", final_data))
        #Find if missed call was recalled
        for idx, call in enumerate(final_data):
            if call['direction'] == "Incoming" and call["disposition"] == "MISSED":
                callback = list(filter(lambda d: d['dst'] in call['src'] and d['calldate'] > call['calldate'], outcoming_calls))
                if callback:
                    final_data[idx]["callback"] = {
                        "linkedid": callback[0]['linkedid'],
                        "calldate": callback[0]['calldate'],
                        "src": callback[0]['src'],
                        "before_call": (callback[0]['calldate'] - call['calldate']).total_seconds()
                    }

        incoming_missed_callback_calls=list(filter(lambda d: d['disposition'] == "MISSED" and d['direction'] == "Incoming" , final_data))
        #Add information about missed calls to outgoing
        for idx, call in enumerate(final_data):
            if call['direction'] == "Outgoing" and call['disposition'] == "ANSWERED":
                missed_calls = list(filter(lambda d: call['dst'] in d['src']
                                               and d['calldate'] < call['calldate']
                                               and d['callback']['linkedid'] == call['linkedid'] , incoming_missed_callback_calls))
                if missed_calls:
                    missed_calls_array = []
                    for missed_call in missed_calls:
                        missed_data = {
                            "calldate": missed_call['calldate'],
                            "src": missed_call['src'],
                            "before_call": (call['calldate']-missed_call['calldate']).total_seconds()
                        }
                        missed_calls_array.append(missed_data)
                    final_data[idx]["missed"] = missed_calls_array

        if DEBUG:
            print("--- Final data parsing execution time %s seconds ---" % (time.time() - start_time))

    except exc.OperationalError as e:
        raise

    return final_data
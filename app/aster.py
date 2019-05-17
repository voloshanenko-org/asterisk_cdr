import socket
from asterisk.ami import AMIClient, SimpleAction
from app import app
import re; re._pattern_type = re.Pattern
from time import sleep
from random import SystemRandom
from string import ascii_uppercase, digits
import json

asterisk_host = app.config.get("ASTERISK_HOST")
asterisk_ami_username = app.config.get("ASTERISK_AMI_USERNAME")
asterisk_ami_password = app.config.get("ASTERISK_AMI_PASSWORD")

GLOBAL_SIP_STATUS_TABLE = {}

def get_asterisk_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)

    if not asterisk_host or not asterisk_ami_username or not asterisk_ami_password:
        raise ValueError('{"error": "PBX_NOT_SET"  }')

    try:
        sock.connect((asterisk_host, 5038))
        sock.close()
    except socket.error as e:
        raise ValueError('{"error": "PBX_NOT_AVAILABLE"  }')

    asterisk_client = AMIClient(address=asterisk_host, port=5038)
    try:
        login_request = asterisk_client.login(username=asterisk_ami_username, secret=asterisk_ami_password)
    except Exception as e:
        asterisk_client.logoff()
        raise ValueError('{"error": "PBX_NOT_AVAILABLE"  }')

    if not login_request.response or login_request.response.is_error():
        asterisk_client.logoff()
        raise ValueError('{"error": "PBX_AUTH_FAILED"  }')

    return asterisk_client


def get_sip_status(sip_extension):
    try:
        ami_client=get_asterisk_client()
    except ValueError as e:
        return e.args[0]

    random_id = ''.join(SystemRandom().choice(ascii_uppercase + digits) for _ in range(12))
    sip_extension_status_action = SimpleAction(
        'PJSIPShowEndpoint',
        Endpoint=sip_extension,
        ActionID = random_id
    )

    ami_client.add_event_listener(
        event_listener, white_list=['EndpointDetail','EndpointDetailComplete']
    )

    ami_client.send_action(sip_extension_status_action, callback=None)

    time_limit = 1
    time_past = 0

    while time_past < time_limit:
        if random_id not in GLOBAL_SIP_STATUS_TABLE:
            time_past += 0.1
            sleep(0.1)
        else:
            ami_client.logoff()
            sip_status = GLOBAL_SIP_STATUS_TABLE[random_id][sip_extension]
            GLOBAL_SIP_STATUS_TABLE.pop(random_id)
            if sip_status in ["Unavailable"]:
                return '{"error": "' + sip_status + '"}'
            else:
                return '{"status": "' + sip_status + '"}'

    if not random_id not in GLOBAL_SIP_STATUS_TABLE:
        ami_client.logoff()
        return '{"error": "SIP_STATUS_TIMEOUT"}'


def get_all_sip_status():
    try:
        ami_client=get_asterisk_client()
    except ValueError as e:
        return e.args[0]

    random_id = ''.join(SystemRandom().choice(ascii_uppercase + digits) for _ in range(12))
    all_sip_status_action = SimpleAction(
        'PJSIPShowEndpoints',
        ActionID = random_id
    )

    ami_client.add_event_listener(
        event_listener, white_list=['EndpointList','EndpointListComplete']
    )

    ami_client.send_action(all_sip_status_action, callback=None)

    time_limit = 30
    time_past = 0

    while time_past < time_limit:
        if random_id in GLOBAL_SIP_STATUS_TABLE and any("status" in d for d in GLOBAL_SIP_STATUS_TABLE[random_id]):
            ami_client.logoff()
            all_sip_data = GLOBAL_SIP_STATUS_TABLE[random_id]
            final_sip_status = []
            for sip_data in all_sip_data:
                final_sip_status.append(sip_data)
            GLOBAL_SIP_STATUS_TABLE.pop(random_id)
            return final_sip_status
        else:
            time_past += 0.1
            sleep(0.1)

    if not random_id not in GLOBAL_SIP_STATUS_TABLE:
        ami_client.logoff()
        return '{"error": "SIP_STATUS_TIMEOUT"}'


def event_listener(event,**kwargs):

    if event.name == "EndpointDetail":
        GLOBAL_SIP_STATUS_TABLE[event.keys["ActionID"]] = { event.keys["ObjectName"] : event["DeviceState"] }
    elif event == "EndpointDetailComplete":
        pass
    elif event.name == "EndpointList":
        if not event.keys["ActionID"] in GLOBAL_SIP_STATUS_TABLE:
            GLOBAL_SIP_STATUS_TABLE[event.keys["ActionID"]] = []
        if not event.keys["ObjectName"] == "anonymous":
            GLOBAL_SIP_STATUS_TABLE[event.keys["ActionID"]].append({ "id": event.keys["ObjectName"], "device_state" : event["DeviceState"] })
    elif event.name == "EndpointListComplete":
        GLOBAL_SIP_STATUS_TABLE[event.keys["ActionID"]].append({ "status" : event["EventList"] })

def run_call(ext, to_num):
    try:
        ami_client=get_asterisk_client()
    except ValueError as e:
        return e.args[0]

    sip = 'PJSIP/{}'.format(ext)
    tel = '{}'.format(to_num)

    call_action = SimpleAction(
        'Originate',
        Channel=sip,
        Exten=tel,
        Priority=1,
        Context='from-internal',
        CallerID='<Call_to_' + to_num  + ">",
    )

    operator_status=json.loads(get_sip_status(ext))

    if "error" in operator_status:
        return '{"error": "OPERATOR_OFFLINE"}'
    elif "status" in operator_status:
        if operator_status["status"] == "In use":
            return '{"error": "OPERATOR_BUSY"}'
        elif operator_status["status"] == "Not in use":
            call_init_request = ami_client.send_action(call_action, callback=None)
            if call_init_request.response and call_init_request.response.is_error():
                ami_client.logoff()
                if call_init_request.response.keys["Message"] == "Originate failed":
                    return '{"error": "PBX_CALL_FAILED" }'
                else:
                    return '{"error": ' + call_init_request.response.keys["Message"] + ' }'
            else:
                ami_client.logoff()
                return '{"result": "CALL_ORIGINATED"}'
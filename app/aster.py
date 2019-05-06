import socket
from asterisk.ami import AMIClient, SimpleAction
from app import app

def run_call(ext, to):
    sip = 'PJSIP/{}'.format(ext)
    tel = '{}'.format(to)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)

    asterisk_host = app.config.get("ASTERISK_HOST")
    asterisk_ami_username = app.config.get("ASTERISK_AMI_USERNAME")
    asterisk_ami_password = app.config.get("ASTERISK_AMI_PASSWORD")

    if not asterisk_host or not asterisk_ami_username or not asterisk_ami_password:
        return '{"error": "PBX_NOT_SET"  }'

    try:
        sock.connect((asterisk_host, 5038))
    except socket.error as e:
        return '{"error": "PBX_NOT_AVAILABLE"  }'
    sock.close()

    client = AMIClient(address=asterisk_host, port=5038)
    login_request = client.login(username=asterisk_ami_username, secret=asterisk_ami_password)
    if login_request.response.is_error():
        client.logoff()
        return '{"error": "PBX_AUTH_FAILED"  }'

    endpoint_status_action = SimpleAction(
        'ExtensionState',
        Exten="920"
    )
    res = endpoint_status_request = client.send_action(endpoint_status_action, callback=None)

    call_action = SimpleAction(
        'Originate',
        Channel=sip,
        Exten=tel,
        Priority=1,
        Context='from-internal',
        CallerID='crmdancer',
    )

    call_init_request = client.send_action(call_action, callback=None)
    if call_init_request.response.is_error():
        client.logoff()
        if call_init_request.response.keys["Message"] == "Originate failed":
            return '{"error": "PBX_CALL_FAILED" }'
        else:
            return '{"error": ' + call_init_request.response.keys["Message"] + ' }'
    else:
        client.logoff()
        return call_init_request.response


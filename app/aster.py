import socket
from asterisk.ami import AMIClient, SimpleAction


def run_call(ext, to):
    sip = 'SIP/{}'.format(ext)
    tel = '9{}'.format(to)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    ats1 = 'f1.ats.com'
    ats2 = 'f2.ats.com'
    host = ats1
    try:
        sock.connect((ats1, 5038))
    except socket.error:
        host = ats2
    sock.close()
    client = AMIClient(address=host, port=5038)
    client.login(username='login', secret='pass')
    action = SimpleAction(
        'Originate',
        Channel=sip,
        Exten=tel,
        Priority=1,
        Context='from-internal',
        CallerID='crmdancer',
    )
    client.send_action(action, callback=None)
    client.logoff()

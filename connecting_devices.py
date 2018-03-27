import pexpect
from passwords import network_device_password

LOGIN, PASSWORD, ENABLE_PASSWORD = network_device_password()


def connect_cisco_router(ip_device):
    t = pexpect.spawn(f'ssh {LOGIN}@{ip_device}', timeout=30)
    i = t.expect([pexpect.TIMEOUT, '[Pp]assword'])
    if i == 0:
        print(f"{ip_device} - Недоступен")
        return False
    t.sendline(PASSWORD)
    i = t.expect(['[Pp]assword', '>', '#'])
    if i == 0:
        print("Неверный пароль!")
        #t.sendline('')
        #i = t.expect(['[Pp]assword', '>', '#'])
        if i == 0:
            print("Я не знаю пароль")
            return False
    if i == 1:
        t.sendline("enable")
        if t.expect(['[Pp]assword', '#' ]) == 0:
            t.sendline(ENABLE_PASSWORD)
            if t.expect(['[Pp]assword', '#']) == 0:
                print("Я не знаю ENABLE пароль")
                return False
    t.sendline('terminal length 0')
    t.expect('#')
    return t


def command_send(t, command):
    t.sendline(command)
    t.expect('#')
    lines = str(t.before)
    #print(lines.replace('\\r\\n\\r\\n', '\\r\\n').replace('\\r\\n', '\n').replace(f'b\'{command}', command))
    return lines.replace('\\r\\n\\r\\n', '\\r\\n').replace('\\r\\n', '\n').replace(f'b\'{command}', command)






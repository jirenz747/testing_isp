import re
import requests
from connecting_devices import command_send
from connecting_devices import connect_cisco_router
from passwords import get_ip_address
from passwords import get_service_desc_password
from myslq import sql_query_all

PING_REPEAT = 10
EXT_PING_REPEAT = 100
PING_SIZE = 1400
PROVIDER_SPEED = 500000

IP_COD_BEELINE, IP_COD_PROSTOR, IP_COD_DOMRU, IP_COD_INET = get_ip_address()
SERVICE_LOGIN, SERVICE_PASS = get_service_desc_password()

INTERVAL_PROBLEM_OBJECT = 1

t = None
full_text = ''

def main():
    global t
    answer = sql_query_all("select t2.shop_obj, t2.shop_obj_name, t2.shop_address, t2.shop_ip, t1.provider_name, t1.provider_ip, t1.our_ip, t1.date_start_problem, t1.billingID, t1.id "
                           f"FROM providers t1 INNER JOIN shops t2 ON t1.shop_id = t2.shop_id where t1.status_problem = 0 and (date_add(t1.date_start_problem, interval {INTERVAL_PROBLEM_OBJECT} minute) < now())  and (t1.date_end_problem IS NULL)");

    for li in answer:
        global full_text
        full_text = ''
        obj, obj_name, address, ip_addr, provider, pe, ce, _, billing, *_ = li
        print(obj, obj_name, address, ip_addr, provider, pe, ce, billing)
        print('#' * 20)
        intraservice(obj_name)
        t = connect_cisco_router(ip_addr)

        if(show_int_load(provider, PROVIDER_SPEED)):
            print(obj_name, provider, 'Имеется загрузка канала')
            #continue

        #command_send('sh ver')
        i, text, *_ = test_ping(f'ping {pe} repeat {PING_REPEAT} source {ce} size {PING_SIZE} timeout 1')
        if i == False:
            full_text += f"{obj}#" + text + '\nШлюз провайдера недоступен!'
            print(full_text)
            continue

        i, text, avr, lose_percent, *_ = test_ping(f'ping {pe} repeat {EXT_PING_REPEAT} source {ce} size {PING_SIZE} timeout 1')
        full_text += f"{obj}#" + text + '\n' + '#' * 20 + '\n'

        if 'beeline' in provider.lower():
            test_to_cod(IP_COD_BEELINE, ce, obj)
        elif 'prostor' in provider.lower():
            print("We are here PROSTOR")
            test_to_cod(IP_COD_PROSTOR, ce, obj)
        elif 'domru' in provider.lower():
            test_to_cod(IP_COD_DOMRU, ce, obj)
        else:
            test_to_cod(IP_COD_INET, ce, obj)
        print(full_text)


def test_to_cod(cod_ip, ce, obj):
    global full_text
    i, text, *_ = test_ping(f'ping {cod_ip} repeat {PING_REPEAT} source {ce} size {PING_SIZE} timeout 1')
    if i == False:
        full_text += f"{obj}#" + text + '\nНет доступности до нашего Цод!'

        return
    i, text, avr, lose_percent, *_ = test_ping(f'ping {cod_ip} repeat {EXT_PING_REPEAT} source {ce} size {PING_SIZE} timeout 1')
    full_text += f"{obj}#" + text + '\n' + '#' * 20 + '\n'
    return

def test_ping(test):
    #print(test)
    global t
    out = command_send(test)
    match = re.search('\d+\/(\d+)\/\d+', out)
    match_2 = re.search('percent \((\d+)\/(\d+)\)', out)
    avr = None
    if not match:
        return [False, out, avr, match_2.group(1), match_2.group(2)]
    avr = match.group(1)
    return [True, out, avr, match_2.group(1), match_2.group(2)]


# Возвращает FALSE, если загрузки канала нет.
def show_int_load(provider,speed):
    # int_tun_1 = None
    # int_tun_2 = None

    provider = provider.lower()
    print(provider)
    if 'beeline' in provider:
        int_tun_1 = command_send('show int tun17')
        int_tun_2 = command_send('show int tun27')
    elif 'domru' in provider:
        int_tun_1 = command_send('show int tun41')
        int_tun_2 = command_send('show int tun51')
    elif 'prostor' in provider:
        int_tun_1 = command_send('show int tun61')
        int_tun_2 = command_send('show int tun71')
    else:
        int_tun_1 = command_send('show int tun1')
        int_tun_2 = command_send('show int tun2')
    #print(int_tun_1)
    #print(int_tun_2)

    # int_tun_1_input = 0
    # int_tun_1_output = 0
    # int_tun_2_input = 0
    # int_tun_2_output = 0
    match = re.search('input rate (\d+) ', int_tun_1)
    int_tun_1_input = match.group(1)
    match = re.search('output rate (\d+) ', int_tun_1)
    int_tun_1_output = match.group(1)
    match = re.search('input rate (\d+) ', int_tun_2)
    int_tun_2_input = match.group(1)
    match = re.search('output rate (\d+) ', int_tun_2)
    int_tun_2_output = match.group(1)
    #print('#' * 10)
    #print(type(int_tun_1_input), int_tun_1_output)
    #print(int_tun_2_input, int_tun_2_output)
    #print('#' * 10)
    if(int(int_tun_1_input) > speed or int(int_tun_1_output) > speed or int(int_tun_2_input) > speed or int(int_tun_2_output)> speed):
        return True
    return False


def intraservice(obj_name):
    obj_name = obj_name.replace(' ', '%20')

    response = requests.get(f'http://{SERVICE_LOGIN}:{SERVICE_PASS}@co-hd.modis.ru/api/task?fields=Id,Name,StatusId,Creator,ServiceId,Description&search="{obj_name}"&ServiceId=348')
    s = response.content.decode()
    if '"StatusId":31' in s:
        print('Заявка открыта!')
        return True
    elif '"StatusId":27' in s:
        print('Заявка в процессе!')
        return True
    elif '"StatusId":35' in s:
        print('Заявка требует уточнения!')
        return True
    elif '"StatusId":43' in s:
        print('Заявка в статусе тестирование!')
        return True
    elif '"StatusId":40' in s:
        print('Не подтверждено выполнение!')
        return True
    elif 'Could not connect' in s:
        print('Интрасервис недоступен!')
        return True
    elif 'Time out' in s:
        print('Интрасервис не отвечает!')
        return True
    return False

main()

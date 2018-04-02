import re
import requests
from connecting_devices import command_send
from connecting_devices import connect_cisco_router
from passwords import get_ip_address
from passwords import get_service_desc_password
from myslq import sql_query_all
from send_email import send_email

PING_REPEAT = 10
EXT_PING_REPEAT = 100  # Расширенный пинг, используется, если обычный прошел удачно
PING_SIZE = 1400  # Размер отправляемых пакетов
PROVIDER_SPEED = 500000  # Максимально допустимая загрузка канала,
# после данного значения скрипт будет думать, что канал загружен.
# По идее необходимо сформировать в БД, для кажого провайдера свою скорость и считать среднее значение

MAXIMUM_LOSTS_PACKETS = 3  # Допустимое количество потерянных пакетов. После чего канал считается неработоспособным
MAXIMUM_DELAY = 300  # Допустимая задержка для канала

IP_COD_BEELINE, IP_COD_PROSTOR, IP_COD_DOMRU, IP_COD_INET = get_ip_address()
SERVICE_LOGIN, SERVICE_PASS = get_service_desc_password()

INTERVAL_PROBLEM_OBJECT = 1

# Глобальные переменные
t = None  # Переменная для подключения к оборудованию.
full_text = ''
result = ''
###

def main():
    global t
    answer = sql_query_all("select t2.shop_obj, t2.shop_obj_name, t2.shop_address, t2.shop_ip, t1.provider_name, t1.provider_ip, t1.our_ip, t1.date_start_problem, t1.billingID, t1.id "
                           f"FROM providers t1 INNER JOIN shops t2 ON t1.shop_id = t2.shop_id where t1.status_problem = 0 and (date_add(t1.date_start_problem, interval {INTERVAL_PROBLEM_OBJECT} minute) < now())  and (t1.date_end_problem IS NULL)");

    for li in answer:
        global EXT_PING_REPEAT
        global full_text
        global result
        full_text = ''
        ip_cod = ''
        obj, obj_name, address, ip_addr, provider, pe, ce, _, billing, *_ = li
        print('\n\n', obj, obj_name, address, ip_addr, provider, pe, ce, billing)
        if intraservice(obj_name):
            continue
        t = connect_cisco_router(ip_addr)
        i, rate_input, rate_output = get_int_load(provider, PROVIDER_SPEED)
        if(i):
            print(obj_name, provider, f'Имеется загрузка канала:\nInput:{rate_input}\nOutput:{rate_output}')
            continue

        if 'beeline' in provider.lower():
            ip_cod = IP_COD_BEELINE
            full_text = 'ID канала: ' + billing + '\n'
        elif 'prostor' in provider.lower():
            ip_cod = IP_COD_PROSTOR
        elif 'domru' in provider.lower():
            ip_cod = IP_COD_DOMRU
        else:
            ip_cod = IP_COD_INET

        full_text += f'Начинаем проверку каналов на объекте: {obj_name} по адресу - {address}\n'
        full_text += '#' * 80 + '\n'
        full_text += f'Проверка из магазина до шлюза провайдера - {provider}\n'
        i, text, *_ = test_ping(f'ping {pe} repeat {PING_REPEAT} source {ce} size {PING_SIZE} timeout 1')
        if i == False:
            full_text += f"{obj}#" + text + '\n' + '#' * 80 + '\nШлюз провайдера недоступен!\n'
            result = 'Result: Шлюз провайдера недоступен!'
            traceroute(f'traceroute ip {ip_cod} source {ce} timeout 1 ttl 1 5 numeric')
            print(full_text)
            if intraservice(obj_name):
                continue
            send_email(f'{obj_name} {address}', full_text, result)
            continue

        i, text, avr, lose_percent, *_ = test_ping(f'ping {pe} repeat {EXT_PING_REPEAT} source {ce} size {PING_SIZE} timeout 1')
        full_text += f"{obj}#" + text + '\n' + '#' * 80 + '\n'
        full_text += '\n' + '#' * 80 + '\n'
        full_text += f'Проверка доступности канала до нашего ЦОДа через {provider}:\n'
        i, text, avr, success_packet, all_packet =  test_to_cod(ip_cod, ce, obj)

        if not i:
            full_text += f"{obj}#" + text + '\n' + '#' * 80 + '\nНет доступности до нашего ЦОДа!\n'
            traceroute(f'traceroute ip {ip_cod} source {ce} timeout 1 ttl 1 5 numeric')
            print(full_text)
            if intraservice(obj_name):
                continue
            send_email(f'{obj_name} {address}', full_text, result)
            continue
        if (int(avr) < 300) and (int(success_packet) > EXT_PING_REPEAT - 30):
            EXT_PING_REPEAT = 200
            i, text, avr, success_packet, all_packet = test_to_cod(ip_cod, ce, obj)
            full_text += f"{obj}#" + text + '\n' + '#' * 80 + '\n'
            EXT_PING_REPEAT = 100

        #print(rate_input, int(rate_output), success_packet, all_packet)
        traceroute(f'traceroute ip {ip_cod} source {ce} timeout 1 ttl 1 5 numeric')
        number_lost_packet = int(all_packet) - int(success_packet)
        if number_lost_packet >= MAXIMUM_LOSTS_PACKETS:
            result = f'Result: Замечены потери трафика. Количество потеряных пакетов {number_lost_packet}'
            full_text += f'Замечены потери трафика. Количество потеряных пакетов {number_lost_packet}\n'
            full_text += 'При этом загрузка канала составляет:\nInput: {:.2f} Kbit'.format(rate_input / 1024)
            full_text += '\nOutput: {:.2f} Kbit\n'.format(rate_output / 1024)
            if intraservice(obj_name):
                continue
            send_email(f'{obj_name} {address}', full_text, result)
        elif int(avr) > MAXIMUM_DELAY:
            result = f'Result: Слишком большие задержки. Задержки составляют {avr}'
            full_text +=  f'Слишком большие задержки. Задержка составляет {avr}\n'
            full_text += 'При этом загрузка канала составляет:\nInput: {:.2f} Kbit'.format(rate_input / 1024)
            full_text += '\nOutput: {:.2f} Kbit\n'.format(rate_output / 1024)
            if intraservice(obj_name):
                continue
            send_email(f'{obj_name} {address}', full_text, result)
        print(full_text)


def test_to_cod(cod_ip, ce, obj):
    global full_text
    global result
    i, out, avr, success_packet, all_packet = test_ping(f'ping {cod_ip} repeat {PING_REPEAT} source {ce} size {PING_SIZE} timeout 1')
    if i == False:
        result = 'Result: Нет доступности до нашего ЦОДа!'
        return [i, out, avr, success_packet, all_packet]
    i, out, avr, success_packet, all_packet = test_ping(f'ping {cod_ip} repeat {EXT_PING_REPEAT} source {ce} size {PING_SIZE} timeout 1')
    return [i, out, avr, success_packet, all_packet]


def test_ping(test):
    global t
    out = command_send(test)
    match = re.search('\d+\/(\d+)\/\d+', out)
    match_2 = re.search('percent \((\d+)\/(\d+)\)', out)
    avr = None
    if not match:
        return [False, out, avr, match_2.group(1), match_2.group(2)]
    avr = match.group(1)
    return [True, out, avr, match_2.group(1), match_2.group(2)]


def traceroute(test):
    global t
    global full_text
    full_text += '\n' + '#' * 80 + '\n'
    out = command_send(test)
    full_text += out
    full_text += '\n' + '#' * 80 + '\n'
    return out


# Возвращает FALSE, если загрузки канала нет.
def get_int_load(provider,speed):
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
    match = re.search('input rate (\d+) ', int_tun_1)
    int_tun_1_input = int(match.group(1))
    match = re.search('output rate (\d+) ', int_tun_1)
    int_tun_1_output = int(match.group(1))
    match = re.search('input rate (\d+) ', int_tun_2)
    int_tun_2_input = int(match.group(1))
    match = re.search('output rate (\d+) ', int_tun_2)
    int_tun_2_output = int(match.group(1))
    #print('\nInput: ', int_tun_1_input + int_tun_2_input)
    #print('Ouput: ', int_tun_1_output + int_tun_2_output)
    if (int_tun_1_input > speed or int_tun_1_output > speed or int_tun_2_input > speed or int_tun_2_output > speed):
        return [True, int_tun_1_input + int_tun_2_input, int_tun_1_output + int_tun_2_output]
    return [False, int_tun_1_input + int_tun_2_input, int_tun_1_output + int_tun_2_output]


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

import requests
import re
from myslq import sql_query
from myslq import sql_update
from myslq import sql_query_all
from passwords import get_nagios_password
import excel

NAGIOS_LOGIN, NAGIOS_PASSWORD, NAGIOS_SERVER = get_nagios_password()


def add_providers(shop_obj, providers_ip, shop_id, billing):
    provider = excel.get_list_provider_ip(shop_obj, providers_ip)
    if provider:
        provider_name, _, ce, pe = provider
        print(f"Добавляем провайдера {provider}")
        sql_update(
            f'insert into providers (shop_id, provider_name, provider_ip, our_ip, date_start_problem, status_problem, billingID) '
            f'values ({shop_id}, "{provider_name}", "{pe}", "{ce}", now(), false, "{billing}")')
        return True
        # print(full_name, network, address)
    else:
        print(f"*{shop_obj} - {providers_ip} - IP провайдера не найден в файле Network no pass")
        return False


response = requests.get(
    f"http://{NAGIOS_LOGIN}:{NAGIOS_PASSWORD}@{NAGIOS_SERVER}/nagios/cgi-bin/status.cgi?servicegroup=ISP1_AND_ISP2&style" \
    "=detail&servicestatustypes=16&hoststatustypes=15&serviceprops=0&hostprops=0")
s = response.content.decode()

obj = {}
l_status_object = re.findall("class='status(\w+)'.+host=(\w+\d+\-gw)'", s)
l_link = re.findall("class='statusBGCRITICAL'><a href='(.+)'>", s)
l_providers = []
count = 0
print('#'*20, 'START','#' *20, "\n")
for host_status, host_obj in l_status_object:
    if str(host_status).lower() in 'hostdown':
        print(host_status, host_obj)
        if sql_query(f"SELECT * FROM shops WHERE shop_obj = '{host_obj}' and shop_status != 'HOSTDOWN'") != False:
            print(f"Update odject {host_obj}")
            sql_update(f'UPDATE shops SET shop_status ="HOSTDOWN" WHERE shop_obj = "{host_obj}"')
    else:
        if not host_obj in l_link[count]:
            count += 1
        response = requests.get(f"http://{NAGIOS_LOGIN}:{NAGIOS_PASSWORD}@{NAGIOS_SERVER}/nagios/cgi-bin/{l_link[count]}")
        page = response.content.decode()
        match = re.search('<p>(\d+\.\d+\.\d+\.\d+).+</p>', page)
        obj[host_obj] = {'ip': match.group(1)}
        obj[host_obj]['status'] = host_status
    count += 1

for shop_obj in obj.keys():
    providers_ip = obj[shop_obj]['ip']
    l_providers.append(obj[shop_obj]['ip'])
    status = obj[shop_obj]['status']
    #Если объект не создан, то создаем его
    provider = None
    if sql_query(f"SELECT * FROM shops WHERE shop_obj = '{shop_obj}'") == False:
        if excel.exist_object(shop_obj):
            print(f"Добавляем объект {shop_obj} в базу данных")
            full_name, network, address, billing = excel.get_list_object(shop_obj)
            sql_update(
                f'INSERT INTO shops (shop_obj, shop_obj_name, shop_status, shop_current_status, shop_address, shop_ip) '
                f'values ("{shop_obj}", "{full_name}", "{status}", false, "{address}", "{network}")')
            shop_id = list(sql_query(f'SELECT * FROM shops where shop_obj = "{shop_obj}"'))[0]
            add_providers(shop_obj, providers_ip, shop_id, billing)
            continue
        else:
            print(f"*Объект {shop_obj} - Не найден в файле Network no pass")
            continue

    answer = sql_query(f'select * from providers t1 inner join shops t2 on t1.shop_id = t2.shop_id where t2.shop_obj ="{shop_obj}" and t1.status_problem = 0 and t1.our_ip = "{providers_ip}"')

    if answer is False:
        #print(answer, "\n\n")
        print(f"Изменяем статус для объекта {shop_obj} - <{providers_ip}>")
        sql_update(f'update shops set shop_status = "Even" where shop_obj = "{shop_obj}"')
        shop_id = list(sql_query(f'SELECT * FROM shops where shop_obj = "{shop_obj}"'))[0]
        _, _, _, billing = excel.get_list_object(shop_obj)
        add_providers(shop_obj, providers_ip, shop_id, billing)

answer = list(sql_query_all('SELECT * FROM shops WHERE shop_status != "NORMAL"'))
for li in answer:
    triger = True
    li = list(li)
    for _, host in l_status_object:
        if li[1] in host:
            #print(li, host)
            triger = False
    if triger:
        print(li[1], " Теперь имеет статус NORMAL")
        sql_update(f'UPDATE shops SET shop_status = "NORMAL" WHERE shop_id = {li[0]}')

answer = list(sql_query_all('SELECT * FROM providers WHERE status_problem = 0'))
for li in answer:
    triger = True
    li = list(li)
    #print(li)
    for ip in l_providers:
        #print(li[4], ip)
        if ip in li[4]:
            triger = False
    if triger:
        print(li[2], li[4], " Провайдер теперь имеет статус NORMAL")
        sql_update(f'UPDATE providers SET date_end_problem = now(), status_problem = 1 WHERE id = {li[0]} and status_problem = 0')

print('#' * 20, 'END', '#' * 20, "\n")
#print(l_status_object)

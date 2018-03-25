
from connecting_devices import command_send
from connecting_devices import connect_cisco_router
from myslq import sql_query_all

answer = sql_query_all("select t2.shop_obj, t2.shop_obj_name, t2.shop_address, t2.shop_ip, t1.provider_name, t1.provider_ip, t1.our_ip, t1.date_start_problem, t1.billingID, t1.id "
                       "FROM providers t1 INNER JOIN shops t2 ON t1.shop_id = t2.shop_id where t1.status_problem = 0 and (date_add(t1.date_start_problem, interval 5 minute) < now())  and (t1.date_end_problem IS NULL)");

for li in answer:
    obj, obj_name, address, ip_addr, provider, *_ = li
    print(ip_addr)


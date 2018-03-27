
from connecting_devices import command_send
from connecting_devices import connect_cisco_router
from myslq import sql_query_all


def main():
    answer = sql_query_all("select t2.shop_obj, t2.shop_obj_name, t2.shop_address, t2.shop_ip, t1.provider_name, t1.provider_ip, t1.our_ip, t1.date_start_problem, t1.billingID, t1.id "
                           "FROM providers t1 INNER JOIN shops t2 ON t1.shop_id = t2.shop_id where t1.status_problem = 0 and (date_add(t1.date_start_problem, interval 5 minute) < now())  and (t1.date_end_problem IS NULL)");
    PING_REPEAT = 10
    PING_SIZE = 1400
    for li in answer:
        obj, obj_name, address, ip_addr, provider, pe, ce, _, billing, *_ = li
        print(obj, obj_name, address, ip_addr, provider, pe, ce, billing)
        print('#' * 20)
        t = connect_cisco_router(ip_addr)
        #command_send('sh ver')
        test_ping(t, f'ping {pe} repeat {PING_REPEAT} source {ce} size {PING_SIZE} timeout 1')
        print('#' * 20, '\n\n')



def test_ping(t, test):
    #print(test)
    out = command_send(t, test)
    print(out)


main()

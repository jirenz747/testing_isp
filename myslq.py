import MySQLdb
from passwords import mysql_password

MYSQL_USER, MYSQL_PASS, MYSQL_SERVER = mysql_password()
connection = MySQLdb.connect(MYSQL_SERVER, MYSQL_USER, MYSQL_PASS, 'shops', charset="utf8", use_unicode=True)
cursor = connection.cursor()

def sql_query(query):
    cursor.execute(query)
    answer = cursor.fetchone()
    if answer is None:
        return False
    else:
        return answer

def sql_update(query):
    cursor.execute(query)
    connection.commit()

def sql_query_all(query):
    cursor.execute(query)
    answer = cursor.fetchall()
    if answer is None:
        return False
    else:
        return answer

# answer = sql_query("SELECT * FROM shops where shop_obj = 'mos2-gw'")
#answer = sql_query(f'select * from providers t1 inner join shops t2 on t1.shop_id = t2.shop_id where t2.shop_obj ="ptg2-gw" and t1.status_problem = 0 and t1.our_ip = "172.16.41.9"')
#print(answer)
import MySQLdb
from passwords import get_mysql_password

MYSQL_USER, MYSQL_PASS, MYSQL_SERVER = get_mysql_password()
connection = MySQLdb.connect(MYSQL_SERVER, MYSQL_USER, MYSQL_PASS, 'shops_test', charset="utf8", use_unicode=True)
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

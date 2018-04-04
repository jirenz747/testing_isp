def get_mysql_password():
    MYSQL_PASS = 'root'
    MYSQL_SERVER = 'localhost'
    MYSQL_USER = 'root'
    return [MYSQL_USER,  MYSQL_PASS, MYSQL_SERVER]


def get_nagios_password():
    NAGIOS_LOGIN = 'login'
    NAGIOS_PASSWORD = 'pass'
    NAGIOS_SERVER = 'ip_server'
    return [NAGIOS_LOGIN, NAGIOS_PASSWORD, NAGIOS_SERVER]


def get_network_device_password():
    LOGIN = 'login'
    PASSWORD = 'password'
    ENABLE_PASSWORD = 'enable_password'
    return [LOGIN, PASSWORD, ENABLE_PASSWORD]


def get_service_desc_password():
    SERVICE_DESK_LOGIN = 'login'
    SERVICE_DESK_PASSWORD = 'password'
    return [SERVICE_DESK_LOGIN,  SERVICE_DESK_PASSWORD]

# IP адреса для IPVPN в нашем ЦОД и для вшнего адреса
def get_ip_address():
    IP_COD_BEELINE = '1.1.1.1' 
    IP_COD_PROSTOR = '2.2.2.2'
    IP_COD_DOMRU = '3.3.3.3'
    IP_COD_INET = '4.4.4.4'
    return [IP_COD_BEELINE, IP_COD_PROSTOR, IP_COD_DOMRU, IP_COD_INET]

# Список email адресов, которые должны получать письма.
def get_email_address():
    return ['email1@yourdomain.ru', 'email2@yourdomain.ru']

import mysql.connector
from mysql.connector import errorcode

config = {
    'user': 'root',
    'password': '8uupvpR8%',
    'host': '127.0.0.1',
    'port': 3306,
}

DB_NAME = 'sportsphere_db'

try:
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET 'utf8mb4' COLLATE 'utf8mb4_unicode_ci';")
    print(f"Database '{DB_NAME}' ensured exists.")
    cursor.close()
    cnx.close()
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Access denied: check your MySQL username or password")
    else:
        print(err)
    raise

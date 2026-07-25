import os
from pathlib import Path

from dotenv import load_dotenv
import mysql.connector
from mysql.connector import errorcode

# Load environment variables from .env file
load_dotenv(Path(__file__).resolve().parent / ".env")

config = {
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'host': os.environ.get('MYSQL_HOST', '127.0.0.1'),
    'port': int(os.environ.get('MYSQL_PORT', '3306')),
}

DB_NAME = os.environ.get('MYSQL_DATABASE', 'sportsphere_db')

if not config['password']:
    print('Error: MYSQL_PASSWORD is not set in .env file')
    raise SystemExit(1)

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


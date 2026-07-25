import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import mysql.connector as mc

# Load environment variables from .env file
load_dotenv(Path(__file__).resolve().parent / ".env")


def main() -> int:
    host = os.environ.get('MYSQL_HOST', '127.0.0.1')
    user = os.environ.get('MYSQL_USER', 'root')
    password = os.environ.get('MYSQL_PASSWORD')
    database = os.environ.get('MYSQL_DATABASE', 'sportsphere_db')
    port = int(os.environ.get('MYSQL_PORT', '3306'))

    if not password:
        print('Error: MYSQL_PASSWORD is not set in .env file')
        return 1

    try:
        connection = mc.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
        )
    except Exception as e:
        print(f'Database is not Connected: {e}')
        return 1

    print('Database is fully Connected')
    connection.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())


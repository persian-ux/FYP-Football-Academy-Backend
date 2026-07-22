import os
import sys

import mysql.connector as mc


def main() -> int:
    host = os.environ.get('MYSQL_HOST', '127.0.0.1')
    user = os.environ.get('MYSQL_USER', 'root')
    password = os.environ.get('MYSQL_PASSWORD', '8uupvpR8%')
    database = os.environ.get('MYSQL_DATABASE', 'sportsphere_db')
    port = int(os.environ.get('MYSQL_PORT', '3306'))

    try:
        connection = mc.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
        )
    except Exception:
        print('Database is not Connected')
        return 1

    print('Database is fully Connected')
    connection.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

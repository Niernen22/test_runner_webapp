import csv
from werkzeug.security import generate_password_hash
import oracledb
import config

def create_user(username):
    username = username.upper()
    password = 'Almafa_123'
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    dsn = config.dsn
    user = config.username
    pwd = config.password

    try:
        pool = oracledb.create_pool(user=user, password=pwd, dsn=dsn, min=1, max=5, increment=1)
        connection = pool.acquire()

        sql = """
        INSERT INTO users (username, password, is_admin)
        VALUES (:username, :password, :is_admin)
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, username=username, password=hashed_password, is_admin=0)  # is_admin is 0 for non-admin user
            connection.commit()

    except Exception as e:
        print(f"Error creating user {username}: {e}")

    finally:
        if 'connection' in locals():
            connection.close()
        if 'pool' in locals():
            pool.close()

def create_users_from_csv(csv_file):
    try:
        with open(csv_file, newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                username = row[0]  # Assuming the username is in the first column
                create_user(username)
    except Exception as e:
        print(f"Error reading CSV file: {e}")

if __name__ == '__main__':
    csv_file = 'usernames.csv'  # Change this to your CSV file path
    create_users_from_csv(csv_file)

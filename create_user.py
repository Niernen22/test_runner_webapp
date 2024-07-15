from werkzeug.security import generate_password_hash
import oracledb
import config

def create_user():
    username = 'admin'
    password = 'adminpassword_123'
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
            cursor.execute(sql, username=username, password=hashed_password, is_admin=1)  # Assuming is_admin is 1 for admin user
            connection.commit()

    except Exception as e:
        print(f"Error creating user: {e}")

    finally:
        if 'connection' in locals():
            connection.close()
        if 'pool' in locals():
            pool.close()

if __name__ == '__main__':
    create_user()

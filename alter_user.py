from werkzeug.security import generate_password_hash
import oracledb
import config

def update_password():
    username = 'username'.upper()
    password = 'Almafa_123'
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    dsn = config.dsn
    user = config.username
    pwd = config.password

    try:
        pool = oracledb.create_pool(user=user, password=pwd, dsn=dsn, min=1, max=5, increment=1)
        connection = pool.acquire()

        sql = """
        UPDATE users
        SET password = :password
        WHERE username = :username
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, username=username, password=hashed_password)
            connection.commit()

    except Exception as e:
        print(f"Error updating password: {e}")

    finally:
        if 'connection' in locals():
            connection.close()
        if 'pool' in locals():
            pool.close()

if __name__ == '__main__':
    update_password()

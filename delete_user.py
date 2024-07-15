import oracledb
import config
from main import User, app

def delete_user(username):
    with app.app_context():
        dsn = config.dsn
        user = config.username
        pwd = config.password

        try:
            pool = oracledb.create_pool(user=user, password=pwd, dsn=dsn, min=1, max=5, increment=1)
            connection = pool.acquire()

            sql = """
            DELETE FROM users
            WHERE username = :username
            """

            with connection.cursor() as cursor:
                cursor.execute(sql, username=username)
                rows_deleted = cursor.rowcount
                connection.commit()

                if rows_deleted > 0:
                    print(f"User '{username}' deleted successfully.")
                else:
                    print(f"User '{username}' not found.")

        except Exception as e:
            print(f"Error deleting user: {e}")

        finally:
            if 'connection' in locals():
                connection.close()
            if 'pool' in locals():
                pool.close()

if __name__ == '__main__':
    delete_user('testuser')

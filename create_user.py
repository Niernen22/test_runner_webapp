from werkzeug.security import generate_password_hash
from main import app, db, User

def create_user():
    with app.app_context():
        username = 'testuser2'
        password = 'password123'
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        user = User(username=username, password=hashed_password, is_admin=False)
        db.session.add(user)
        db.session.commit()

if __name__ == '__main__':
    create_user()

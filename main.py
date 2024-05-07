from flask import Flask, render_template, abort
import oracledb
import config

app = Flask(__name__)

username = 'sartasnadi'
password = 'password'
dsn='rstodsdev1.develop:1521/RDWD'

connection = oracledb.connect(user=username, password=password, dsn=dsn)

@app.route('/favicon.ico')
def favicon():
    abort(404)

@app.route('/')
def index():
    try:
        cursor = connection.cursor()

        query = "SELECT * FROM TESTS"
        cursor.execute(query)
        tests = cursor.fetchall()

        cursor.close()

        return render_template('index.html', tests=tests)
    
    except oracledb.Error as error:
        return f"Error connecting to Oracle DB: {error}"

@app.route('/test_steps/<test_id>')
def test_steps(test_id):
    try:
        cursor = connection.cursor()

        query = "SELECT * FROM TEST_STEPS WHERE TEST_ID = :test_id"
        cursor.execute(query, test_id=test_id)
        test_steps_data = cursor.fetchall()

        cursor.close()

        return render_template('test_steps.html', test_id=test_id, test_steps=test_steps_data)
    
    except cx_Oracle.Error as error:
        return f"Error retrieving test steps: {error}"

if __name__ == '__main__':
    app.run(debug=True)

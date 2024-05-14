from flask import Flask, render_template, abort, request, redirect, url_for
from datetime import datetime
from threading import Thread
import json
import oracledb
import config

app = Flask(__name__)

username = config.username
password = config.password
dsn = config.dsn

pool = oracledb.create_pool(user=username, password=password, dsn=dsn,
                            min=1, max=5, increment=1)


@app.route('/favicon.ico')
def favicon():
    abort(404)

@app.route('/')
def index():
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        query = "SELECT * FROM TESTS ORDER BY NAME"
        cursor.execute(query)
        tests = cursor.fetchall()

        cursor.close()

        return render_template('index.html', tests=tests)
    
    except oracledb.Error as error:
        return f"Error connecting to Oracle DB: {error}"


@app.route('/job_details')
def job_details():
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        query = "SELECT * FROM TEST_RUN_LOG ORDER BY RUN_ID DESC"
        cursor.execute(query)
        job_details = cursor.fetchall()

        cursor.close()

        return render_template('job_details.html', job_details=job_details)

    except oracledb.Error as error:
        return f"Error connecting to Oracle DB: {error}"


@app.route('/job_steps_details')
def job_steps_details():
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        query = "SELECT * FROM STEP_RUN_LOG ORDER BY RUN_ID DESC"
        cursor.execute(query)
        job_steps_details = cursor.fetchall()

        cursor.close()

        return render_template('job_steps_details.html', job_steps_details=job_steps_details)

    except oracledb.Error as error:
        return f"Error connecting to Oracle DB: {error}"
        

@app.route('/test_steps/<test_id>')
def test_steps(test_id):
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        query = "SELECT * FROM TEST_STEPS WHERE TEST_ID = :test_id ORDER BY ID"
        cursor.execute(query, test_id=test_id)
        test_steps_data = cursor.fetchall()

        cursor.close()

        return render_template('test_steps.html', test_id=test_id, test_steps=test_steps_data)
    
    except oracledb.Error as error:
        return f"Error retrieving test steps: {error}"


@app.route('/edit_steps/<test_id>')
def edit_steps(test_id):
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        query = "SELECT * FROM TEST_STEPS WHERE TEST_ID = :test_id ORDER BY ID"
        cursor.execute(query, test_id=test_id)
        test_steps_data = cursor.fetchall()

        sql = "SELECT USERNAME FROM DBA_USERS"
        cursor.execute(sql)
        usernames = [row[0] for row in cursor.fetchall()]

        cursor.close()

        return render_template('edit_steps.html', test_id=test_id, test_steps=test_steps_data, usernames=usernames)

    except oracledb.Error as error:
        return f"Error retrieving test steps: {error}"


@app.route('/add_step', methods=['POST'])
def add_step():

    if request.method == 'POST':
        new_id = request.form['new_id']
        new_test_id = request.form['new_test_id']
        new_step_name = request.form['new_step_name']
        new_order_number = request.form['new_order_number']
        new_type = request.form['new_type']
        new_sql_code = request.form['new_sql_code']
        new_target_user = request.form['new_target_user']

    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        sql = "INSERT INTO TEST_STEPS (ID, TEST_ID, NAME, ORDERNUMBER, STATUS, TYPE, SQL_CODE, TARGET_USER) VALUES (:1, :2, :3, :4, :5, :6, :7, :8)"
        data = (new_id, new_test_id, new_step_name, new_order_number, 'ADDED', new_type, new_sql_code, new_target_user)

        cursor.execute(sql, data)
        connection.commit()

        cursor.close()

        return redirect(url_for('edit_steps', test_id=new_test_id))

    except oracledb.Error as error:
        return f"Error retrieving test steps: {error}"


@app.route('/delete_step', methods=['POST'])
def delete_step():
    try:
        id = request.form['id']
        test_id = request.form['test_id'] 
        connection = pool.acquire()
        cursor = connection.cursor()

        sql = "DELETE FROM TEST_STEPS WHERE ID = :id"
        cursor.execute(sql, {'id': id})
        connection.commit()
        cursor.close()

        return redirect(url_for('edit_steps', test_id=test_id))

    except oracledb.Error as error:
        return f"Error deleting step: {error}"

@app.route('/add', methods=['GET'])
def add():
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT USERNAME FROM DBA_USERS"
        cursor.execute(sql)
        usernames = [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return render_template('add.html', usernames=usernames)
    except Exception as e:
        return render_template('add.html', error=str(e))

@app.route('/get_tables_for_schema', methods=['POST'])
def get_tables_for_schema():
    selected_schema = request.json['schema']
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT table_name FROM all_tables WHERE owner = :schema"
        cursor.execute(sql, {'schema': selected_schema})
        table_names = [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(table_names)
    except Exception as e:
        return json.dumps({'error': str(e)})

@app.route('/get_workdays', methods=['GET'])
def get_workdays():
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT DISTINCT(T_DATE) FROM STA.TR_DATE WHERE WORK_DAY = 'Y'"
        cursor.execute(sql)
        workdays = [row[0].strftime("%Y-%m-%d") for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(workdays)
    except Exception as e:
        return json.dumps({'error': str(e)})



def run_test_async(test_id):
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        cursor.callproc('test_package.TEST_RUNNER')

        connection.commit()
        cursor.close()

        print("Test successfully executed!")

    except oracledb.Error as error:
        print(f"Error running test: {error}") 

@app.route('/run_test/<test_id>')
def run_test(test_id):
    Thread(target=run_test_async, args=(test_id,)).start()

    return redirect(url_for('test_steps', test_id=test_id))


if __name__ == '__main__':
    app.run(debug=True)

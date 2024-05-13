from flask import Flask, render_template, abort, request, redirect, url_for
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

        cursor.close()

        return render_template('edit_steps.html', test_id=test_id, test_steps=test_steps_data)

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



@app.route('/run_test/<test_id>')
def run_test(test_id):
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        cursor.callproc('test_package.TEST_RUNNER')

        connection.commit()
        cursor.close()

        return "Test successfully executed!"

    except oracledb.Error as error:
        return f"Error running test: {error}"


if __name__ == '__main__':
    app.run(debug=True)

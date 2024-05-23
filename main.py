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

        query = "SELECT * FROM STEP_RUN_LOG ORDER BY RUN_ID DESC, STEP_ID DESC"
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

        sql = "SELECT MODULE FROM LM.INV_JOBS"
        cursor.execute(sql)
        modules = [row[0] for row in cursor.fetchall()]

        sql = "SELECT DISTINCT(OBJECT_NAME) FROM DBA_PROCEDURES WHERE OBJECT_TYPE IN ('FUNCTION' , 'PROCEDURE')"
        cursor.execute(sql)
        storedobject_names = [row[0] for row in cursor.fetchall()]

        sql = "SELECT DISTINCT(OWNER) FROM DBA_PROCEDURES"
        cursor.execute(sql)
        procedures_schemas = [row[0] for row in cursor.fetchall()]

        sql = "SELECT PROCEDURE_NAME FROM DBA_PROCEDURES WHERE OBJECT_TYPE = 'PACKAGE'"
        cursor.execute(sql)
        storedpackage_names = [row[0] for row in cursor.fetchall()]

        cursor.close()

        return render_template('edit_steps.html', test_id=test_id, test_steps=test_steps_data, usernames=usernames, modules=modules, storedobject_names=storedobject_names, procedures_schemas=procedures_schemas, storedpackage_names=storedpackage_names)

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


@app.route('/get_procedures_for_schema', methods=['POST'])
def get_procedures_for_schema():
    selected_schema = request.json['schema']
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT OBJECT_NAME FROM DBA_PROCEDURES WHERE OBJECT_TYPE IN ('FUNCTION', 'PROCEDURE') AND OWNER = :schema"
        cursor.execute(sql, {'schema': selected_schema})
        procedure_names = [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(procedure_names)
    except Exception as e:
        return json.dumps({'error': str(e)})


@app.route('/get_parameters_for_stored_procedure', methods=['POST'])
def get_parameters_for_stored_procedure():
    selectedSchema = request.json['schema']
    selectedStoredObjectName = request.json['storedobject_name']
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT argument_name, data_type, defaulted, default_value FROM dba_arguments WHERE IN_OUT = 'IN' AND object_name = :storedobject_name AND owner = :schema"
        cursor.execute(sql, {'storedobject_name': selectedStoredObjectName, 'schema': selectedSchema})
        parameter_details = [{'argument_name': row[0], 'data_type': row[1], 'defaulted': row[2], 'default_value': row[3]} for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(parameter_details)
    except Exception as e:
        return json.dumps({'error': str(e)})


@app.route('/get_parameters_for_stored_procedure_in_package', methods=['POST'])
def get_parameters_for_stored_procedure_in_package():
    selectedStoredObjectName = request.json['storedobject_name']
    selectedSchema = request.json['schema']
    selectedPackage = request.json['package_name']
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT argument_name, data_type, defaulted, default_value FROM dba_arguments WHERE IN_OUT = 'IN' AND object_name = :storedobject_name AND package_name = :package_name AND owner = :schema"
        cursor.execute(sql, {'storedobject_name': selectedStoredObjectName, 'package_name': selectedPackage, 'schema': selectedSchema})
        parameter_details = [{'argument_name': row[0], 'data_type': row[1], 'defaulted': row[2], 'default_value': row[3]} for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(parameter_details)
    except Exception as e:
        return json.dumps({'error': str(e)})


@app.route('/get_packages_for_schema', methods=['POST'])
def get_packages_for_schema():
    selected_schema = request.json['schema']
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT OBJECT_NAME FROM DBA_PROCEDURES WHERE OBJECT_TYPE = 'PACKAGE' AND OWNER = :schema"
        cursor.execute(sql, {'schema': selected_schema})
        package_names = [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(package_names)
    except Exception as e:
        return json.dumps({'error': str(e)})


@app.route('/get_procedures_for_package', methods=['POST'])
def get_procedures_for_package():
    selected_package = request.json['package']
    selected_schema = request.json['schema']
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT PROCEDURE_NAME FROM DBA_PROCEDURES WHERE OBJECT_TYPE = 'PACKAGE' AND OWNER = :schema AND OBJECT_NAME = :package"
        cursor.execute(sql, {'schema': selected_schema, 'package': selected_package})
        procedure_names = [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(procedure_names)
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


@app.route('/get_names_for_module', methods=['POST'])
def get_names_for_module():
    selected_module = request.json['module']
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT NAME FROM LM.INV_JOBS WHERE MODULE = :module"
        cursor.execute(sql, {'module': selected_module})
        names = [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(names)
    except Exception as e:
        return json.dumps({'error': str(e)})


@app.route('/get_types_for_module', methods=['POST'])
def get_types_for_module():
    selected_module = request.json['module']
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT TYPE FROM LM.INV_MODULE WHERE MODULE = :module"
        cursor.execute(sql, {'module': selected_module})
        types = [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(types)
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

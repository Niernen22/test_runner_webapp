from flask import Flask, render_template, request, redirect, url_for, jsonify
from threading import Thread
import json
import oracledb
import config
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

secret_key = config.secret_key

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

username = config.username
password = config.password
dsn = config.dsn

pool = oracledb.create_pool(user=username, password=password, dsn=dsn, min=1, max=5, increment=1)

class User(UserMixin):
    def __init__(self, id, username, password, is_admin):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    connection = pool.acquire()
    cursor = connection.cursor()
    query = "SELECT id, username, password, is_admin FROM users WHERE id = :id"
    cursor.execute(query, {'id': user_id})
    row = cursor.fetchone()
    if row:
        user = User(row[0], row[1], row[2], bool(row[3]))
    else:
        user = None
    cursor.close()
    pool.release(connection)
    return user

@app.route('/manage_users')
@login_required
def manage_users():
    connection = pool.acquire()
    cursor = connection.cursor()
    query = "SELECT id, username, password, is_admin FROM users"
    cursor.execute(query)
    users = []
    for row in cursor:
        users.append(User(row[0], row[1], row[2], bool(row[3])))
    cursor.close()
    pool.release(connection)
    return render_template('manage_users.html', users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        connection = pool.acquire()
        cursor = connection.cursor()
        query = "SELECT id, username, password, is_admin FROM users WHERE username = :username"
        cursor.execute(query, {'username': username})
        row = cursor.fetchone()
        cursor.close()
        pool.release(connection)
        if row and check_password_hash(row[2], password):
            user = User(row[0], row[1], row[2], bool(row[3]))
            login_user(user)
            return redirect(url_for('index'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        return "Access denied", 403

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = bool(request.form.get('is_admin'))

        connection = pool.acquire()
        cursor = connection.cursor()
        insert_query = "INSERT INTO users (username, password, is_admin) VALUES (:username, :password, :is_admin)"
        cursor.execute(insert_query, {'username': username, 'password': generate_password_hash(password), 'is_admin': is_admin})
        connection.commit()
        cursor.close()
        pool.release(connection)

        return redirect(url_for('manage_users'))

    return render_template('add_user.html')

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return "Access denied", 403

    connection = pool.acquire()
    cursor = connection.cursor()
    delete_query = "DELETE FROM users WHERE id = :id"
    cursor.execute(delete_query, {'id': user_id})
    connection.commit()
    cursor.close()
    pool.release(connection)

    return redirect(url_for('manage_users'))


@app.errorhandler(404)
def page_not_found(error):
    return "Page not found", 404


@app.route('/')
@login_required
def index():
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        search_name = request.args.get('search_name')

        if search_name:
            query = "SELECT * FROM TESTS WHERE NAME LIKE '%' || :search_name || '%' ORDER BY NAME"
            cursor.execute(query, {'search_name': search_name})
        else:
            query = "SELECT * FROM TESTS ORDER BY NAME"
            cursor.execute(query)

        tests = []
        column_names = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            tests.append(dict(zip(column_names, row)))

        cursor.close()
        connection.close()

        return render_template('index.html', tests=tests)

    except oracledb.Error as error:
        return f"Error connecting to Oracle DB: {error}"

@app.route('/add_test', methods=['POST'])
@login_required
def add_test():
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        new_id_query = "SELECT MAX(ID) FROM TESTS"
        cursor.execute(new_id_query)
        result = cursor.fetchone()
        new_id = (result[0] if result[0] is not None else 0) + 1

        test_name = request.form['new_test_name']

        query = "INSERT INTO TESTS (ID, NAME) VALUES (:id, :name)"
        cursor.execute(query, {'id': new_id, 'name': test_name})

        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for('edit_steps', test_id=new_id))

    except oracledb.Error as error:
        return f"Error inserting new test: {error}"




@app.route('/job_details')
@login_required
def job_details():
    try:
        run_id_filter = request.args.get('run_id')

        connection = pool.acquire()
        cursor = connection.cursor()

        if run_id_filter:
            query = "SELECT * FROM TEST_RUN_LOG WHERE RUN_ID = :run_id ORDER BY EVENT_TIME DESC"
            cursor.execute(query, {'run_id': run_id_filter})
        else:
            query = "SELECT * FROM TEST_RUN_LOG ORDER BY EVENT_TIME DESC"
            cursor.execute(query)

        job_details = []
        column_names = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            job_details.append(dict(zip(column_names, row)))

        cursor.close()

        return render_template('job_details.html', job_details=job_details)

    except oracledb.Error as error:
        return f"Error connecting to Oracle DB: {error}"


@app.route('/job_steps_details')
@login_required
def job_steps_details():
    try:
        run_id_filter = request.args.get('run_id')

        connection = pool.acquire()
        cursor = connection.cursor()

        if run_id_filter:
            query = "SELECT * FROM STEP_RUN_LOG WHERE RUN_ID = :run_id ORDER BY EVENT_TIME DESC"
            cursor.execute(query, {'run_id': run_id_filter})
        else:
            query = "SELECT * FROM STEP_RUN_LOG ORDER BY EVENT_TIME DESC"
            cursor.execute(query)

        job_steps_details = []
        column_names = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            job_steps_details.append(dict(zip(column_names, row)))

        cursor.close()

        return render_template('job_steps_details.html', job_steps_details=job_steps_details)

    except oracledb.Error as error:
        return f"Error connecting to Oracle DB: {error}"


        

@app.route('/test_steps/<test_id>')
@login_required
def test_steps(test_id):
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        query = "SELECT * FROM TEST_STEPS WHERE TEST_ID = :test_id ORDER BY ORDERNUMBER"
        cursor.execute(query, test_id=test_id)

        test_steps_data = []
        column_names = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            test_steps_data.append(dict(zip(column_names, row)))

        cursor.close()

        return render_template('test_steps.html', test_id=test_id, test_steps=test_steps_data)
    
    except oracledb.Error as error:
        return f"Error retrieving test steps: {error}"



@app.route('/edit_steps/<test_id>')
@login_required
def edit_steps(test_id):
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        query = "SELECT * FROM TEST_STEPS WHERE TEST_ID = :test_id ORDER BY ORDERNUMBER"
        cursor.execute(query, test_id=test_id)
        test_steps_data = []
        column_names = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            test_steps_data.append(dict(zip(column_names, row)))

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


@app.route('/update_order', methods=['POST'])
@login_required
def update_order():
    data = request.get_json()
    
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        for item in data:
            query = "UPDATE TEST_STEPS SET ORDERNUMBER = :order_number WHERE ID = :id"
            cursor.execute(query, order_number=item['order_number'], id=item['id'])

        connection.commit()
        
        return jsonify({"success": True}), 200

    except Exception as e:
        print(e)
        return jsonify({"success": False}), 500

    finally:
        cursor.close()
        connection.close()



@app.route('/add_step/<test_id>', methods=['POST'])
@login_required
def add_step(test_id):
    
    try:
        if request.is_json:
            data = request.get_json()
        else:
            return jsonify({'success': False, 'error': 'Invalid input format'})

        new_step_name = data.get('new_step_name')
        step_type = data.get('step_type')
        sql_code = ''
        target_user = 'STA_TEST'
       
        def default_if_none(value, default=''):
            return value if value is not None else default

        if step_type == 'TABLECOPY':
            source_schema = default_if_none(data.get('source_schema'))
            source_table = default_if_none(data.get('source_table'))
            target_schema = default_if_none(data.get('target_schema'))
            target_table = default_if_none(data.get('target_table'))
            truncate = default_if_none(data.get('truncate'))
            chosen_date = default_if_none(data.get('date'))
        
            sql_code = f"""
            BEGIN 
                TABLECOPY_PACKAGE.TABLECOPY(
                    '{source_schema}', 
                    '{source_table}', 
                    '{target_schema}', 
                    '{target_table}', 
                    '{truncate}', 
                    TO_DATE('{chosen_date}', 'yyyy-mm-dd')
                ); 
            END;
            """
        
        elif step_type == 'LM_JOB':
            module = default_if_none(data.get('module'))
            _type = default_if_none(data.get('type'))
            name = default_if_none(data.get('name'))

            sql_code = f"""
            declare 
                p_result varchar2(4000); 
                p_err_code varchar2(4000); 
                p_output clob; 
            begin 
                lm.{_type}.execute(1, '{module}', '{name}', p_result, p_err_code, p_output, false); 
                dbms_output.put_line(p_result || ' - ' || p_err_code); 
                dbms_output.put_line(p_output); 
            end; 
            """

        elif step_type == 'STORED_PROCEDURE':
            storedprocedure_type = default_if_none(data.get('storedprocedure_type'))
            parameters = ', '.join([f"'{default_if_none(value)}'" for value in data.get('parameters', {}).values()])
            if storedprocedure_type == 'Function_or_Procedure':
                procedures_schema = default_if_none(data.get('procedures_schema'))
                storedobject_name = default_if_none(data.get('storedobject_name'))
                sql_code = f"BEGIN {procedures_schema}.{storedobject_name}({parameters}); END;"
        
            elif storedprocedure_type == 'Package':
                procedures_schema_package = default_if_none(data.get('procedures_schema_package'))
                storedpackage_name = default_if_none(data.get('storedpackage_name'))
                storedobject_name_package = default_if_none(data.get('storedobject_name_package'))
                sql_code = f"BEGIN {procedures_schema_package}.{storedpackage_name}.{storedobject_name_package}({parameters}); END;"

        connection = pool.acquire()
        cursor = connection.cursor()
        
        new_id_query = "SELECT MAX(ID) FROM TEST_STEPS"
        cursor.execute(new_id_query)
        result = cursor.fetchone()
        new_id = (result[0] if result[0] is not None else 0) + 1

        new_order_query = "SELECT MAX(ORDERNUMBER) FROM TEST_STEPS WHERE TEST_ID = :test_id"
        cursor.execute(new_order_query, (test_id,))
        result = cursor.fetchone()
        new_order_number = (result[0] if result[0] is not None else 0) + 1

        sql = "INSERT INTO TEST_STEPS (ID, TEST_ID, NAME, ORDERNUMBER, STATUS, TYPE, SQL_CODE, TARGET_USER) VALUES (:1, :2, :3, :4, :5, :6, :7, :8)"
        data = (new_id, test_id, new_step_name, new_order_number, 'ADDED', step_type, sql_code, target_user)

        cursor.execute(sql, data)
        connection.commit()

        cursor.close()

        return jsonify({'success': True, 'redirect_url': url_for('edit_steps', test_id=test_id)})

    except oracledb.Error as error:
        return jsonify({'success': False, 'error': str(error)})



@app.route('/delete_step', methods=['POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
def get_parameters_for_stored_procedure():
    selectedSchema = request.json['schema']
    selectedStoredObjectName = request.json['storedobject_name']
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT argument_name, data_type, defaulted, default_value FROM dba_arguments WHERE IN_OUT = 'IN' AND PACKAGE_NAME IS NULL AND object_name = :storedobject_name AND owner = :schema"
        cursor.execute(sql, {'storedobject_name': selectedStoredObjectName, 'schema': selectedSchema})
        parameter_details = [{'argument_name': row[0], 'data_type': row[1], 'defaulted': row[2], 'default_value': row[3]} for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(parameter_details)
    except Exception as e:
        return json.dumps({'error': str(e)})


@app.route('/get_parameters_for_stored_procedure_in_package', methods=['POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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

        v_run_id = cursor.callfunc('TEST_PACKAGE.TEST_RUNNER', oracledb.NUMBER, [test_id])

        connection.commit()
        cursor.close()

        print(f"Test started successfully! Run ID: {v_run_id}")

        return {'success': True, 'v_run_id': v_run_id}

    except oracledb.Error as error:
        print(f"Error running test: {error}")
        return {'success': False, 'error': str(error)}

@app.route('/run_test/<test_id>', methods=['POST'])
@login_required
def run_test(test_id):
    result = run_test_async(test_id)
    
    if result['success']:
        return jsonify({'success': True, 'message': 'Test started successfully!', 'v_run_id': result['v_run_id']})
    else:
        return jsonify({'success': False, 'error': result['error']}), 500


if __name__ == '__main__':
    app.run(debug=True)

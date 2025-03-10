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


@app.route('/account')
@login_required
def account():
    return render_template('account.html')


@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']

    connection = pool.acquire()
    cursor = connection.cursor()
    query = "SELECT password FROM users WHERE id = :id"
    cursor.execute(query, {'id': current_user.id})
    row = cursor.fetchone()

    if row and check_password_hash(row[0], current_password):
        update_query = "UPDATE users SET password = :password WHERE id = :id"
        cursor.execute(update_query, {'password': generate_password_hash(new_password), 'id': current_user.id})
        connection.commit()
        cursor.close()
        pool.release(connection)
        return redirect(url_for('index'))
    else:
        cursor.close()
        pool.release(connection)
        return 'Invalid current password', 400




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
            query = "SELECT * FROM TESTS ORDER BY ID DESC"
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

        test_name = request.form['new_test_name']

        query = "INSERT INTO TESTS (ID, NAME) VALUES (TESTS_SEQ.NEXTVAL, :name)"
        cursor.execute(query, {'name': test_name})

        connection.commit()

        cursor.execute("SELECT TESTS_SEQ.CURRVAL FROM dual")
        new_id = cursor.fetchone()[0]

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

        query = """
        SELECT ts.*, 
               (SELECT srl.OUTPUT_MESSAGE
                FROM STEP_RUN_LOG srl 
                WHERE srl.STEP_ID = ts.ID 
                ORDER BY srl.EVENT_TIME DESC 
                FETCH FIRST ROW ONLY) AS LATEST_OUTPUT,
               (SELECT srl.RUN_ID
                FROM STEP_RUN_LOG srl 
                WHERE srl.STEP_ID = ts.ID 
                ORDER BY srl.EVENT_TIME DESC 
                FETCH FIRST ROW ONLY) AS LATEST_RUN_ID
        FROM TEST_STEPS ts
        WHERE ts.TEST_ID = :test_id
        ORDER BY ts.ORDERNUMBER
        """
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

        sql = "SELECT USERNAME FROM DBA_USERS ORDER BY USERNAME ASC"
        cursor.execute(sql)
        usernames = ['-- Select an option --'] + [row[0] for row in cursor.fetchall()]

        sql = "SELECT USERNAME FROM DBA_USERS@ODS_PROD ORDER BY USERNAME ASC"
        cursor.execute(sql)
        prod_usernames = ['-- Select an option --'] + [row[0] for row in cursor.fetchall()]

        sql = "SELECT DISTINCT(MODULE) FROM LM.INV_JOBS ORDER BY MODULE ASC"
        cursor.execute(sql)
        modules = ['-- Select an option --'] + [row[0] for row in cursor.fetchall()]

        sql = "SELECT DISTINCT(OBJECT_NAME) FROM DBA_PROCEDURES WHERE OBJECT_TYPE = 'PROCEDURE' ORDER BY OBJECT_NAME ASC"
        cursor.execute(sql)
        storedobject_names = ['-- Select an option --'] + [row[0] for row in cursor.fetchall()]

        sql = "SELECT DISTINCT(OWNER) FROM DBA_PROCEDURES ORDER BY OWNER ASC"
        cursor.execute(sql)
        procedures_schemas = ['-- Select an option --'] + [row[0] for row in cursor.fetchall()]

        sql = "SELECT DISTINCT(PROCEDURE_NAME) FROM DBA_PROCEDURES WHERE OBJECT_TYPE = 'PACKAGE' ORDER BY PROCEDURE_NAME ASC"
        cursor.execute(sql)
        storedpackage_names = ['-- Select an option --'] + [row[0] for row in cursor.fetchall()]

        cursor.close()

        return render_template('edit_steps.html', test_id=test_id, test_steps=test_steps_data, prod_usernames=prod_usernames, usernames=usernames, modules=modules, storedobject_names=storedobject_names, procedures_schemas=procedures_schemas, storedpackage_names=storedpackage_names)

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
       
        def default_if_none(value, default=''):
            return value if value is not None else default

        def format_parameter(value, data_type):
            if value is None:
                return "NULL"

            data_type = data_type.upper()

            if data_type in ("VARCHAR2", "CHAR", "CLOB", "LONG"):
                escaped_value = value.replace("'", "''")
                return f"'{escaped_value}'"

            elif data_type in ("NUMBER", "INTEGER", "FLOAT", "BINARY_DOUBLE", "BINARY_FLOAT", "BINARY_INTEGER", "PL/SQL BOOLEAN"):
                return str(value)

            elif data_type == "DATE":
                return f"TO_DATE('{value}', 'YYYY-MM-DD')"

            elif data_type == "TIMESTAMP":
                return f"TO_TIMESTAMP('{value}', 'YYYY-MM-DD HH24:MI:SS')"

            else:
                raise ValueError(f"Unsupported data type: {data_type}")

        if step_type == 'TABLECOPY':
            target_user = 'TEST_RUNNER_REPO'
            source_schema = default_if_none(data.get('source_schema'))
            source_table = default_if_none(data.get('source_table'))
            target_schema = default_if_none(data.get('target_schema'))
            target_table = default_if_none(data.get('target_table'))
            truncate = default_if_none(data.get('truncate'))
            chosen_date = default_if_none(data.get('date'))

            if chosen_date is None:
                sql_code = f"""
                BEGIN 
                    TABLECOPY_PACKAGE.TABLECOPY(
                        p_source_schema => '{source_schema}', 
                        p_source_table => '{source_table}', 
                        p_target_schema => '{target_schema}', 
                        p_target_table => '{target_table}', 
                        p_truncate => {truncate}, 
                        p_tnd_filter => NULL
                    ); 
                END;
                """
            else:
                sql_code = f"""
                BEGIN 
                    TABLECOPY_PACKAGE.TABLECOPY(
                        p_source_schema => '{source_schema}', 
                        p_source_table => '{source_table}', 
                        p_target_schema => '{target_schema}', 
                        p_target_table => '{target_table}', 
                        p_truncate => {truncate}, 
                        p_tnd_filter => TO_DATE('{chosen_date}', 'yyyy-mm-dd')
                    ); 
                END;
                """

        elif step_type == 'TRUNCATE_TABLE':
            target_user = 'TEST_RUNNER_REPO'
            truncate_schema = default_if_none(data.get('truncate_schema'))
            truncate_table = default_if_none(data.get('truncate_table'))
            truncate_date = default_if_none(data.get('truncate_date'))

            if truncate_date is None:
                sql_code = f"""
                BEGIN
                    {target_user}.TRUNCATE_TND_TABLE(
                        p_CEL_SEMA => '{truncate_schema}', 
                        p_CEL_TABLA => '{truncate_table}', 
                        p_TND_SZURES => NULL
                    );
                END;
                """
            else:
                sql_code = f"""
                BEGIN
                    {target_user}.TRUNCATE_TND_TABLE(
                        p_CEL_SEMA => '{truncate_schema}', 
                        p_CEL_TABLA => '{truncate_table}', 
                        p_TND_SZURES => TO_DATE('{truncate_date}', 'yyyy-mm-dd')
                    );
                END;
                """

        elif step_type == 'LM_JOB':
            target_user = 'LM'
            module = default_if_none(data.get('module'))
            _type = default_if_none(data.get('type'))
            name = default_if_none(data.get('name'))

            sql_code = f"""
            declare 
                p_result varchar2(4000); 
                p_err_code varchar2(4000); 
                p_output clob; 
            begin 
                lm.{_type}.execute(1, '{module}', q'({name})', p_result, p_err_code, p_output, false); 
                dbms_output.put_line(p_result || ' - ' || p_err_code); 
                dbms_output.put_line(p_output); 
            end; 
            """
        elif step_type == 'STORED_PROCEDURE':
            storedprocedure_type = default_if_none(data.get('storedprocedure_type'))
            parameters = data.get('parameters', [])
            parameter_details = data.get('parameter_details', [])

            sql_declare = [] 
            sql_exec_params = []
            sql_output = [] 

            for param in parameters:
                param_name = param['name']
                param_type = param['type']
                param_value = default_if_none(param['value'])

                param_detail = next((p for p in parameter_details if p['argument_name'] == param_name), None)
                if not param_detail:
                    raise ValueError(f"Parameter detail not found for {param_name}")

                data_type = param_detail['data_type']

                if param_type == 'OUT':
                    sql_declare.append(f"{param_name} {data_type};")
                    sql_exec_params.append(param_name)
                    sql_output.append(f"DBMS_OUTPUT.PUT_LINE({param_name});")

                elif param_type == 'IN/OUT':
                    formatted_value = format_parameter(param_value, data_type)
                    sql_declare.append(f"{param_name} {data_type} := {formatted_value};")
                    sql_exec_params.append(param_name)
                    sql_output.append(f"DBMS_OUTPUT.PUT_LINE({param_name});")

                else:
                    formatted_value = format_parameter(param_value, data_type)
                    sql_exec_params.append(formatted_value)

            declare_section = ""
            if sql_declare:
                declare_section = f"DECLARE\n    {' '.join(sql_declare)}\n"

            if storedprocedure_type == 'SingleProcedure':
                procedures_schema = default_if_none(data.get('procedures_schema'))
                storedobject_name = default_if_none(data.get('storedobject_name'))
                sql_code = f"""
                {declare_section}BEGIN
                    {procedures_schema}.{storedobject_name}({', '.join(sql_exec_params)});
                    {' '.join(sql_output)}
                END;
                """

            elif storedprocedure_type == 'Package':
                procedures_schema_package = default_if_none(data.get('procedures_schema_package'))
                storedpackage_name = default_if_none(data.get('storedpackage_name'))
                storedobject_name_package = default_if_none(data.get('storedobject_name_package'))
                sql_code = f"""
                {declare_section}BEGIN
                    {procedures_schema_package}.{storedpackage_name}.{storedobject_name_package}({', '.join(sql_exec_params)});
                    {' '.join(sql_output)}
                END;
                """

            target_user = procedures_schema if storedprocedure_type == 'SingleProcedure' else procedures_schema_package

        connection = pool.acquire()
        cursor = connection.cursor()

        new_order_query = "SELECT MAX(ORDERNUMBER) FROM TEST_STEPS WHERE TEST_ID = :test_id"
        cursor.execute(new_order_query, {'test_id': test_id})
        result = cursor.fetchone()
        new_order_number = (result[0] if result[0] is not None else 0) + 1

        cursor.execute("SELECT TEST_STEPS_SEQ.NEXTVAL FROM dual")
        new_id = cursor.fetchone()[0] 

        sql = "INSERT INTO TEST_STEPS (ID, TEST_ID, NAME, ORDERNUMBER, STATUS, TYPE, SQL_CODE, TARGET_USER) VALUES (:1, :2, :3, :4, :5, :6, :7, :8)"
        data = (new_id, test_id, new_step_name, new_order_number, 'ADDED', step_type, sql_code, target_user)

        cursor.execute(sql, data)
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'success': True, 'redirect_url': url_for('edit_steps', test_id=test_id)})

    except oracledb.Error as error:
        return jsonify({'success': False, 'error': str(error)})
    except Exception as error:
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
        sql = "SELECT table_name FROM all_tables WHERE owner = :schema order by table_name asc"
        cursor.execute(sql, {'schema': selected_schema})
        table_names = ['-- Select an option --'] + [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(table_names)
    except Exception as e:
        return json.dumps({'error': str(e)})


@app.route('/get_tables_for_prod_schema', methods=['POST'])
@login_required
def get_tables_for_prod_schema():
    selected_schema = request.json['schema']
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT table_name FROM all_tables@ods_prod WHERE owner = :schema order by table_name asc"
        cursor.execute(sql, {'schema': selected_schema})
        table_names = ['-- Select an option --'] + [row[0] for row in cursor.fetchall()]
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
        sql = "SELECT DISTINCT(OBJECT_NAME) FROM DBA_PROCEDURES WHERE OBJECT_TYPE = 'PROCEDURE' AND OWNER = :schema order by object_name asc"
        cursor.execute(sql, {'schema': selected_schema})
        procedure_names = ['-- Select an option --'] + [row[0] for row in cursor.fetchall()]
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

        sql = """
        SELECT argument_name, data_type, defaulted, default_value, IN_OUT 
        FROM dba_arguments 
        WHERE PACKAGE_NAME IS NULL 
          AND object_name = :storedobject_name 
          AND owner = :schema
        """

        cursor.execute(sql, {'storedobject_name': selectedStoredObjectName, 'schema': selectedSchema})

        parameter_details = [
            {
                'argument_name': row[0], 
                'data_type': row[1], 
                'defaulted': row[2], 
                'default_value': row[3], 
                'in_out': row[4]
            } 
            for row in cursor.fetchall()
        ]

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

        sql = """
        SELECT argument_name, data_type, defaulted, default_value, IN_OUT 
        FROM dba_arguments 
        WHERE object_name = :storedobject_name 
          AND package_name = :package_name 
          AND owner = :schema
        """

        cursor.execute(sql, {'storedobject_name': selectedStoredObjectName, 'package_name': selectedPackage, 'schema': selectedSchema})

        parameter_details = [
            {
                'argument_name': row[0], 
                'data_type': row[1], 
                'defaulted': row[2], 
                'default_value': row[3], 
                'in_out': row[4]
            } 
            for row in cursor.fetchall()
        ]

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
        sql = "SELECT OBJECT_NAME FROM DBA_OBJECTS WHERE OBJECT_TYPE = 'PACKAGE BODY' AND OWNER = :schema order by object_name asc"
        cursor.execute(sql, {'schema': selected_schema})
        package_names = ['-- Select an option --'] + [row[0] for row in cursor.fetchall()]
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
        sql = "SELECT PROCEDURE_NAME FROM DBA_PROCEDURES WHERE OBJECT_TYPE = 'PACKAGE' AND PROCEDURE_NAME IS NOT NULL AND OWNER = :schema AND OBJECT_NAME = :package order by procedure_name asc"
        cursor.execute(sql, {'schema': selected_schema, 'package': selected_package})
        procedure_names = ['-- Select an option --'] + [row[0] for row in cursor.fetchall()]
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
        sql = "SELECT T_DATE FROM STA.TR_DATE WHERE WORK_DAY = 'Y' AND T_DATE BETWEEN ADD_MONTHS(TRUNC(SYSDATE, 'YEAR'), -12) AND LAST_DAY(SYSDATE) ORDER BY T_DATE DESC"
        cursor.execute(sql)
        workdays = ['-- Select an option --'] + [row[0].strftime("%Y-%m-%d") for row in cursor.fetchall()]
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
        sql = "SELECT DISTINCT(NAME) FROM LM.INV_JOBS WHERE MODULE = :module order by name asc"
        cursor.execute(sql, {'module': selected_module})
        names = ['-- Select an option --'] + [row[0] for row in cursor.fetchall()]
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
        sql = "SELECT DISTINCT(TYPE) FROM LM.INV_MODULE WHERE MODULE = :module order by type asc"
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

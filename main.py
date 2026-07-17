from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from threading import Thread
import json
import oracledb
import config
from datetime import datetime
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

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        abort(403)
    try:
        page = max(1, request.args.get('page', 1, type=int))
        per_page = 50
        offset = (page - 1) * per_page

        connection = pool.acquire()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM STEP_RUN_LOG srl
            JOIN TEST_STEPS ts ON srl.STEP_ID = ts.ID
            WHERE srl.EVENT NOT IN ('STARTED', 'SUCCEEDED')
        """)
        total = cursor.fetchone()[0]
        total_pages = max(1, -(-total // per_page))

        cursor.execute("""
            SELECT srl.RUN_ID,
                   t.ID     AS TEST_ID,
                   t.NAME   AS TEST_NAME,
                   t.OWNER  AS TEST_OWNER,
                   srl.STEP_ID,
                   srl.STEP_NAME,
                   srl.EVENT,
                   srl.EVENT_TIME,
                   srl.STEP_SQL,
                   srl.ERROR_MESSAGE,
                   srl.OUTPUT_MESSAGE
            FROM STEP_RUN_LOG srl
            JOIN TEST_STEPS ts ON srl.STEP_ID = ts.ID
            JOIN TESTS t ON ts.TEST_ID = t.ID
            WHERE srl.EVENT NOT IN ('STARTED', 'SUCCEEDED')
            ORDER BY srl.EVENT_TIME DESC
            OFFSET :offset ROWS FETCH NEXT :per_page ROWS ONLY
        """, {'offset': offset, 'per_page': per_page})

        columns = [col[0] for col in cursor.description]
        failed_logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return render_template('admin.html', failed_logs=failed_logs,
                               page=page, total_pages=total_pages, total=total)
    except oracledb.Error:
        app.logger.error("Failed to load admin page", exc_info=True)
        abort(500)

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
        username = request.form['username'].upper()
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
        return render_template('login.html', error='Invalid credentials'), 401
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
        abort(403)

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
        abort(403)

    connection = pool.acquire()
    cursor = connection.cursor()
    delete_query = "DELETE FROM users WHERE id = :id"
    cursor.execute(delete_query, {'id': user_id})
    connection.commit()
    cursor.close()
    pool.release(connection)

    return redirect(url_for('manage_users'))

@app.route('/admin_change_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_change_password(user_id):
    if not current_user.is_admin:
        abort(403)

    connection = pool.acquire()
    cursor = connection.cursor()

    if request.method == 'POST':
        new_password = request.form['password']
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')

        cursor.execute("""
            UPDATE users
            SET password = :password
            WHERE id = :user_id
        """, {'password': hashed_password, 'user_id': user_id})
        connection.commit()

        cursor.execute("SELECT id, username FROM users WHERE id = :id", {'id': user_id})
        user = cursor.fetchone()

        cursor.close()
        pool.release(connection)

        return render_template('admin_change_password.html', user=user, success=True)

    cursor.execute("SELECT id, username FROM users WHERE id = :id", {'id': user_id})
    user = cursor.fetchone()
    cursor.close()
    pool.release(connection)

    if not user:
        abort(404)

    return render_template('admin_change_password.html', user=user)




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
        return render_template('account.html', error='Invalid current password'), 400





@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', code=403, title='Forbidden', message='You do not have permission to access this page.'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, title='Not Found', message='The page you are looking for does not exist.'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('error.html', code=500, title='Server Error', message='Something went wrong on our end. Please try again later.'), 500


@app.route('/')
@login_required
def index():
    try:
        page = max(1, request.args.get('page', 1, type=int))
        per_page = 50
        offset = (page - 1) * per_page
        search_name = request.args.get('search_name')

        connection = pool.acquire()
        cursor = connection.cursor()

        if search_name:
            search_name = search_name.upper()
            where = "WHERE ARCHIVED != 'YES' AND OWNER LIKE '%' || :search_name || '%'"
            params = {'search_name': search_name}
        else:
            where = "WHERE ARCHIVED != 'YES'"
            params = {}

        cursor.execute(f"SELECT COUNT(*) FROM TESTS {where}", params)
        total = cursor.fetchone()[0]
        total_pages = max(1, -(-total // per_page))

        cursor.execute(
            f"SELECT * FROM TESTS {where} ORDER BY ID DESC OFFSET :offset ROWS FETCH NEXT :per_page ROWS ONLY",
            {**params, 'offset': offset, 'per_page': per_page}
        )

        column_names = [col[0] for col in cursor.description]
        tests = [dict(zip(column_names, row)) for row in cursor.fetchall()]

        cursor.close()
        connection.close()

        return render_template('index.html', tests=tests, page=page,
                               total_pages=total_pages, total=total,
                               search_name=search_name or '')

    except oracledb.Error as error:
        app.logger.error("Failed to load test list", exc_info=True)
        return "A database error occurred.", 500

@app.route('/add_test', methods=['POST'])
@login_required
def add_test():
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        test_name = request.form['new_test_name']
        owner = current_user.username

        query = "INSERT INTO TESTS (ID, NAME, OWNER, ARCHIVED) VALUES (TESTS_SEQ.NEXTVAL, :name, :owner, 'NO')"
        cursor.execute(query, {'name': test_name, 'owner': owner})

        connection.commit()

        cursor.execute("SELECT TESTS_SEQ.CURRVAL FROM dual")
        new_id = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return redirect(url_for('edit_steps', test_id=new_id))

    except oracledb.Error as error:
        app.logger.error("Failed to insert new test", exc_info=True)
        return "A database error occurred.", 500
        

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
        cursor.execute(query, {'test_id': test_id})

        test_steps_data = []
        column_names = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            test_steps_data.append(dict(zip(column_names, row)))

        cursor.execute("SELECT OWNER FROM TESTS WHERE ID = :test_id", {'test_id': test_id})
        owner_row = cursor.fetchone()
        test_owner = owner_row[0] if owner_row else None

        tnd_query = "SELECT get_tnd FROM dual"
        cursor.execute(tnd_query)
        tnd_data = cursor.fetchone()[0]

        cursor.close()

        return render_template('test_steps.html', test_id=test_id, test_steps=test_steps_data, tnd_data=tnd_data, test_owner=test_owner)

    except oracledb.Error as error:
        app.logger.error("Failed to load test steps view", exc_info=True)
        return "A database error occurred.", 500




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

        sql = "SELECT USERNAME FROM DBA_USERS WHERE USERNAME != 'LM' ORDER BY USERNAME ASC"
        cursor.execute(sql)
        usernames = [row[0] for row in cursor.fetchall()]

        sql = "SELECT USERNAME FROM DBA_USERS@ODS_PROD WHERE USERNAME != 'LM' ORDER BY USERNAME ASC"
        cursor.execute(sql)
        prod_usernames = [row[0] for row in cursor.fetchall()]

        sql = "SELECT DISTINCT(MODULE) FROM LM.INV_JOBS ORDER BY MODULE ASC"
        cursor.execute(sql)
        modules = [row[0] for row in cursor.fetchall()]

        sql = "SELECT DISTINCT(OBJECT_NAME) FROM DBA_PROCEDURES WHERE OBJECT_TYPE = 'PROCEDURE' ORDER BY OBJECT_NAME ASC"
        cursor.execute(sql)
        storedobject_names = [row[0] for row in cursor.fetchall()]

        sql = "SELECT DISTINCT(OWNER) FROM DBA_PROCEDURES ORDER BY OWNER ASC"
        cursor.execute(sql)
        procedures_schemas = [row[0] for row in cursor.fetchall()]

        sql = "SELECT DISTINCT(PROCEDURE_NAME) FROM DBA_PROCEDURES WHERE OBJECT_TYPE = 'PACKAGE' ORDER BY PROCEDURE_NAME ASC"
        cursor.execute(sql)
        storedpackage_names = [row[0] for row in cursor.fetchall()]

        cursor.close()

        return render_template('edit_steps.html', test_id=test_id, test_steps=test_steps_data, prod_usernames=prod_usernames, usernames=usernames, modules=modules, storedobject_names=storedobject_names, procedures_schemas=procedures_schemas, storedpackage_names=storedpackage_names)

    except oracledb.Error as error:
        app.logger.error("Failed to load edit steps view", exc_info=True)
        return "A database error occurred.", 500


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
        app.logger.error("Failed to update step order", exc_info=True)
        return jsonify({"success": False, "error": "A database error occurred."}), 500

    finally:
        cursor.close()
        connection.close()


def _default_if_none(value, default=''):
    return value if value is not None else default

def _format_parameter(value, data_type):
    if value is None:
        return "NULL"
    data_type = data_type.upper()
    if data_type in ("VARCHAR2(100)", "CHAR", "CLOB", "LONG"):
        return f"'{value.replace(chr(39), chr(39)*2)}'"
    if data_type in ("NUMBER", "INTEGER", "FLOAT", "BINARY_DOUBLE", "BINARY_FLOAT", "BINARY_INTEGER", "PL/SQL BOOLEAN"):
        return str(value)
    if data_type == "DATE":
        return f"TO_DATE('{value}', 'YYYY-MM-DD')"
    if data_type == "TIMESTAMP":
        return f"TO_TIMESTAMP('{value}', 'YYYY-MM-DD HH24:MI:SS')"
    raise ValueError(f"Unsupported data type: {data_type}")

def _fix_data_type(data_type):
    if data_type.upper().startswith('VARCHAR2'):
        return 'VARCHAR2(100)'
    return data_type


def _build_tablecopy_sql(data):
    source_schema = _default_if_none(data.get('source_schema'))
    source_table  = _default_if_none(data.get('source_table'))
    target_schema = _default_if_none(data.get('target_schema'))
    target_table  = _default_if_none(data.get('target_table'))
    truncate      = _default_if_none(data.get('truncate'))
    chosen_date   = _default_if_none(data.get('date'))
    row_limit_raw = data.get('row_limit', 0)
    row_limit_sql = 'NULL' if not row_limit_raw or int(row_limit_raw) == 0 else str(int(row_limit_raw))

    if chosen_date == "CURRENT_TND":
        sql_code = f"""
        BEGIN
            TABLECOPY_PACKAGE.TABLECOPY_CURRENT(
                p_source_schema => '{source_schema}',
                p_source_table  => '{source_table}',
                p_target_schema => '{target_schema}',
                p_target_table  => '{target_table}',
                p_truncate      => {truncate},
                p_row_limit     => {row_limit_sql}
            );
        END;
        """
    elif chosen_date == "MAX_TND":
        sql_code = f"""
        BEGIN
            TABLECOPY_PACKAGE.TABLECOPY_MAX(
                p_source_schema => '{source_schema}',
                p_source_table  => '{source_table}',
                p_target_schema => '{target_schema}',
                p_target_table  => '{target_table}',
                p_truncate      => {truncate},
                p_row_limit     => {row_limit_sql}
            );
        END;
        """
    elif not chosen_date:
        sql_code = f"""
        BEGIN
            TABLECOPY_PACKAGE.TABLECOPY(
                p_source_schema => '{source_schema}',
                p_source_table  => '{source_table}',
                p_target_schema => '{target_schema}',
                p_target_table  => '{target_table}',
                p_truncate      => {truncate},
                p_tnd_filter    => NULL,
                p_row_limit     => {row_limit_sql}
            );
        END;
        """
    else:
        sql_code = f"""
        BEGIN
            TABLECOPY_PACKAGE.TABLECOPY(
                p_source_schema => '{source_schema}',
                p_source_table  => '{source_table}',
                p_target_schema => '{target_schema}',
                p_target_table  => '{target_table}',
                p_truncate      => {truncate},
                p_tnd_filter    => TO_DATE('{chosen_date}', 'yyyy-mm-dd'),
                p_row_limit     => {row_limit_sql}
            );
        END;
        """
    return sql_code, 'TEST_RUNNER_REPO'


def _build_truncate_sql(data):
    truncate_schema = _default_if_none(data.get('truncate_schema'))
    truncate_table  = _default_if_none(data.get('truncate_table'))
    truncate_date   = _default_if_none(data.get('truncate_date'))

    if not truncate_date:
        sql_code = f"""
        BEGIN
            TEST_RUNNER_REPO.TRUNCATE_TND_TABLE(
                p_CEL_SEMA   => '{truncate_schema}',
                p_CEL_TABLA  => '{truncate_table}',
                p_TND_SZURES => NULL
            );
        END;
        """
    else:
        sql_code = f"""
        BEGIN
            TEST_RUNNER_REPO.TRUNCATE_TND_TABLE(
                p_CEL_SEMA   => '{truncate_schema}',
                p_CEL_TABLA  => '{truncate_table}',
                p_TND_SZURES => TO_DATE('{truncate_date}', 'yyyy-mm-dd')
            );
        END;
        """
    return sql_code, 'TEST_RUNNER_REPO'


def _build_lm_job_sql(data):
    module = _default_if_none(data.get('module'))
    _type  = _default_if_none(data.get('type'))
    name   = _default_if_none(data.get('name'))

    sql_code = f"""
    DECLARE
        p_result   VARCHAR2(4000);
        p_err_code VARCHAR2(4000);
        p_output   CLOB;
    BEGIN
        lm.{_type}.execute(1, '{module}', q'({name})', p_result, p_err_code, p_output, false);
        DBMS_OUTPUT.PUT_LINE(p_result || ' - ' || p_err_code);
        DBMS_OUTPUT.PUT_LINE(p_output);
    END;
    """
    return sql_code, 'LM'


def _build_stored_procedure_sql(data):
    storedprocedure_type = _default_if_none(data.get('storedprocedure_type'))
    parameters           = data.get('parameters', [])
    parameter_details    = data.get('parameter_details', [])

    sql_declare     = []
    sql_exec_params = []
    sql_output      = []

    for param in parameters:
        param_name  = param['name']
        param_type  = param['type']
        param_value = param['value']

        param_detail = next((p for p in parameter_details if p['argument_name'] == param_name), None)
        if not param_detail:
            raise ValueError(f"Parameter detail not found for {param_name}")

        data_type = _fix_data_type(param_detail['data_type'])

        if param_type == 'OUT':
            sql_declare.append(f"{param_name} {data_type};")
            sql_exec_params.append(f"{param_name} => {param_name}")
            sql_output.append(f"DBMS_OUTPUT.PUT_LINE({param_name});")
        elif param_type == 'IN/OUT':
            formatted_value = _format_parameter(param_value, data_type)
            sql_declare.append(f"{param_name} {data_type} := {formatted_value};")
            sql_exec_params.append(f"{param_name} => {param_name}")
            sql_output.append(f"DBMS_OUTPUT.PUT_LINE({param_name});")
        else:  # IN
            if param_value not in (None, ''):
                formatted_value = _format_parameter(param_value, data_type)
                sql_exec_params.append(f"{param_name} => {formatted_value}")

    declare_section = f"DECLARE\n    {' '.join(sql_declare)}\n" if sql_declare else ""
    params_str      = ', '.join(sql_exec_params)
    output_str      = ' '.join(sql_output)

    if storedprocedure_type == 'SingleProcedure':
        procedures_schema = _default_if_none(data.get('procedures_schema'))
        storedobject_name = _default_if_none(data.get('storedobject_name'))
        sql_code = f"""
        {declare_section}BEGIN
            {procedures_schema}.{storedobject_name}({params_str});
            {output_str}
        END;
        """
        target_user = procedures_schema
    else:  # Package
        procedures_schema_package  = _default_if_none(data.get('procedures_schema_package'))
        storedpackage_name         = _default_if_none(data.get('storedpackage_name'))
        storedobject_name_package  = _default_if_none(data.get('storedobject_name_package'))
        sql_code = f"""
        {declare_section}BEGIN
            {procedures_schema_package}.{storedpackage_name}.{storedobject_name_package}({params_str});
            {output_str}
        END;
        """
        target_user = procedures_schema_package

    return sql_code, target_user


_SQL_BUILDERS = {
    'TABLECOPY':        _build_tablecopy_sql,
    'TRUNCATE_TABLE':   _build_truncate_sql,
    'LM_JOB':           _build_lm_job_sql,
    'STORED_PROCEDURE': _build_stored_procedure_sql,
}


@app.route('/add_step/<test_id>', methods=['POST'])
@login_required
def add_step(test_id):
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Invalid input format'})

        data          = request.get_json()
        new_step_name = data.get('new_step_name')
        step_type     = data.get('step_type')

        if step_type not in _SQL_BUILDERS:
            return jsonify({'success': False, 'error': f'Unknown step type: {step_type}'}), 400

        sql_code, target_user = _SQL_BUILDERS[step_type](data)

        connection = pool.acquire()
        cursor = connection.cursor()

        cursor.execute("SELECT MAX(ORDERNUMBER) FROM TEST_STEPS WHERE TEST_ID = :test_id", {'test_id': test_id})
        result = cursor.fetchone()
        new_order_number = (result[0] if result[0] is not None else 0) + 1

        cursor.execute("SELECT TEST_STEPS_SEQ.NEXTVAL FROM dual")
        new_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO TEST_STEPS (ID, TEST_ID, NAME, ORDERNUMBER, STATUS, TYPE, SQL_CODE, TARGET_USER, ACTIVITY, STEP_PARAMS) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)",
            (new_id, test_id, new_step_name, new_order_number, 'ADDED', step_type, sql_code, target_user, 'ACTIVE', json.dumps(data))
        )
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'success': True, 'redirect_url': url_for('edit_steps', test_id=test_id)})

    except (oracledb.Error, Exception) as error:
        app.logger.error("Failed to add step", exc_info=True)
        return jsonify({'success': False, 'error': 'A database error occurred.'}), 500


@app.route('/get_step_params/<int:step_id>', methods=['GET'])
@login_required
def get_step_params(step_id):
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        cursor.execute("SELECT STEP_PARAMS FROM TEST_STEPS WHERE ID = :id", {'id': step_id})
        row = cursor.fetchone()
        cursor.close()
        pool.release(connection)
        if not row or not row[0]:
            abort(404)
        params_json = row[0].read() if hasattr(row[0], 'read') else row[0]
        return params_json, 200, {'Content-Type': 'application/json'}
    except oracledb.Error:
        app.logger.error("Failed to get step params", exc_info=True)
        return jsonify({'error': 'A database error occurred.'}), 500


@app.route('/edit_step/<int:step_id>', methods=['POST'])
@login_required
def edit_step(step_id):
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Invalid input format'})

        data          = request.get_json()
        new_step_name = data.get('new_step_name')
        step_type     = data.get('step_type')

        if step_type not in _SQL_BUILDERS:
            return jsonify({'success': False, 'error': f'Unknown step type: {step_type}'}), 400

        sql_code, target_user = _SQL_BUILDERS[step_type](data)

        connection = pool.acquire()
        cursor = connection.cursor()

        cursor.execute("SELECT TEST_ID FROM TEST_STEPS WHERE ID = :id", {'id': step_id})
        row = cursor.fetchone()
        if not row:
            abort(404)
        test_id = row[0]

        cursor.execute(
            "UPDATE TEST_STEPS SET NAME = :name, TYPE = :type, SQL_CODE = :sql_code, TARGET_USER = :target_user, STEP_PARAMS = :step_params WHERE ID = :id",
            {'name': new_step_name, 'type': step_type, 'sql_code': sql_code, 'target_user': target_user, 'step_params': json.dumps(data), 'id': step_id}
        )
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'success': True, 'redirect_url': url_for('edit_steps', test_id=test_id)})

    except (oracledb.Error, Exception):
        app.logger.error("Failed to edit step", exc_info=True)
        return jsonify({'success': False, 'error': 'A database error occurred.'}), 500


@app.route('/duplicate_step', methods=['POST'])
@login_required
def duplicate_step():
    try:
        step_id = request.form['id']
        test_id = request.form['test_id']

        connection = pool.acquire()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT NAME, TYPE, SQL_CODE, TARGET_USER, ACTIVITY, STEP_PARAMS FROM TEST_STEPS WHERE ID = :id",
            {'id': step_id}
        )
        row = cursor.fetchone()
        if not row:
            abort(404)

        name, step_type, sql_code, target_user, activity, step_params = row
        if hasattr(step_params, 'read'):
            step_params = step_params.read()

        cursor.execute("SELECT MAX(ORDERNUMBER) FROM TEST_STEPS WHERE TEST_ID = :test_id", {'test_id': test_id})
        result = cursor.fetchone()
        new_order_number = (result[0] if result[0] is not None else 0) + 1

        cursor.execute("SELECT TEST_STEPS_SEQ.NEXTVAL FROM dual")
        new_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO TEST_STEPS (ID, TEST_ID, NAME, ORDERNUMBER, STATUS, TYPE, SQL_CODE, TARGET_USER, ACTIVITY, STEP_PARAMS) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)",
            (new_id, test_id, f"Copy of {name}", new_order_number, 'ADDED', step_type, sql_code, target_user, activity, step_params)
        )
        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for('edit_steps', test_id=test_id))

    except oracledb.Error:
        app.logger.error("Failed to duplicate step", exc_info=True)
        return "A database error occurred.", 500


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
        app.logger.error("Failed to delete step", exc_info=True)
        return "A database error occurred.", 500


@app.route('/step_activity', methods=['POST'])
@login_required
def step_activity():
    try:
        id = request.form['id']
        test_id = request.form['test_id'] 
        connection = pool.acquire()
        cursor = connection.cursor()

        cursor.execute("SELECT ACTIVITY FROM TEST_STEPS WHERE ID = :id", {'id': id})
        current_status = cursor.fetchone()

        if current_status:
            new_status = 'INACTIVE' if current_status[0] != 'INACTIVE' else 'ACTIVE'
            sql = "UPDATE TEST_STEPS SET ACTIVITY = :new_status WHERE ID = :id"
            cursor.execute(sql, {'new_status': new_status, 'id': id})
            connection.commit()

        cursor.close()
        return redirect(url_for('edit_steps', test_id=test_id))

    except oracledb.Error as error:
        app.logger.error("Failed to toggle step activity", exc_info=True)
        return "A database error occurred.", 500


@app.route('/get_tables_for_schema', methods=['GET'])
@login_required
def get_tables_for_schema():
    selected_schema = request.args.get('schema')
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
        app.logger.error("Lookup endpoint error", exc_info=True)
        return json.dumps({'error': 'A database error occurred.'})


@app.route('/get_tables_for_prod_schema', methods=['GET'])
@login_required
def get_tables_for_prod_schema():
    selected_schema = request.args.get('schema')
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT table_name FROM all_tables@ods_prod WHERE owner = :schema"
        cursor.execute(sql, {'schema': selected_schema})
        table_names = [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(table_names)
    except Exception as e:
        app.logger.error("Lookup endpoint error", exc_info=True)
        return json.dumps({'error': 'A database error occurred.'})


@app.route('/get_procedures_for_schema', methods=['GET'])
@login_required
def get_procedures_for_schema():
    selected_schema = request.args.get('schema')
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT DISTINCT(OBJECT_NAME) FROM DBA_PROCEDURES WHERE OBJECT_TYPE = 'PROCEDURE' AND OWNER = :schema order by object_name asc"
        cursor.execute(sql, {'schema': selected_schema})
        procedure_names = [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(procedure_names)
    except Exception as e:
        app.logger.error("Lookup endpoint error", exc_info=True)
        return json.dumps({'error': 'A database error occurred.'})


@app.route('/get_parameters_for_stored_procedure', methods=['GET'])
@login_required
def get_parameters_for_stored_procedure():
    selectedSchema = request.args.get('schema')
    selectedStoredObjectName = request.args.get('storedobject_name')
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
        app.logger.error("Lookup endpoint error", exc_info=True)
        return json.dumps({'error': 'A database error occurred.'})


@app.route('/get_parameters_for_stored_procedure_in_package', methods=['GET'])
@login_required
def get_parameters_for_stored_procedure_in_package():
    selectedStoredObjectName = request.args.get('storedobject_name')
    selectedSchema = request.args.get('schema')
    selectedPackage = request.args.get('package_name')
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
        app.logger.error("Lookup endpoint error", exc_info=True)
        return json.dumps({'error': 'A database error occurred.'})



@app.route('/get_packages_for_schema', methods=['GET'])
@login_required
def get_packages_for_schema():
    selected_schema = request.args.get('schema')
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT OBJECT_NAME FROM DBA_OBJECTS WHERE OBJECT_TYPE = 'PACKAGE BODY' AND OWNER = :schema order by object_name asc"
        cursor.execute(sql, {'schema': selected_schema})
        package_names = [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(package_names)
    except Exception as e:
        app.logger.error("Lookup endpoint error", exc_info=True)
        return json.dumps({'error': 'A database error occurred.'})


@app.route('/get_procedures_for_package', methods=['GET'])
@login_required
def get_procedures_for_package():
    selected_package = request.args.get('package')
    selected_schema = request.args.get('schema')
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT PROCEDURE_NAME FROM DBA_PROCEDURES WHERE OBJECT_TYPE = 'PACKAGE' AND PROCEDURE_NAME IS NOT NULL AND OWNER = :schema AND OBJECT_NAME = :package order by procedure_name asc"
        cursor.execute(sql, {'schema': selected_schema, 'package': selected_package})
        procedure_names = [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(procedure_names)
    except Exception as e:
        app.logger.error("Lookup endpoint error", exc_info=True)
        return json.dumps({'error': 'A database error occurred.'})


@app.route('/get_workdays', methods=['GET'])
@login_required
def get_workdays():
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT T_DATE FROM STA.TR_DATE WHERE WORK_DAY = 'Y' AND T_DATE BETWEEN ADD_MONTHS(TRUNC(SYSDATE, 'YEAR'), -12) AND LAST_DAY(SYSDATE) ORDER BY T_DATE DESC"
        cursor.execute(sql)
        workdays = [row[0].strftime("%Y-%m-%d") for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(workdays)
    except Exception as e:
        app.logger.error("Lookup endpoint error", exc_info=True)
        return json.dumps({'error': 'A database error occurred.'})


@app.route('/get_names_for_module', methods=['GET'])
@login_required
def get_names_for_module():
    selected_module = request.args.get('module')
    try:
        connection = pool.acquire()
        cursor = connection.cursor()
        sql = "SELECT DISTINCT(NAME) FROM LM.INV_JOBS WHERE MODULE = :module order by name asc"
        cursor.execute(sql, {'module': selected_module})
        names = [row[0] for row in cursor.fetchall()]
        cursor.close()
        pool.release(connection)
        return json.dumps(names)
    except Exception as e:
        app.logger.error("Lookup endpoint error", exc_info=True)
        return json.dumps({'error': 'A database error occurred.'})


@app.route('/get_types_for_module', methods=['GET'])
@login_required
def get_types_for_module():
    selected_module = request.args.get('module')
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
        app.logger.error("Lookup endpoint error", exc_info=True)
        return json.dumps({'error': 'A database error occurred.'})



def run_test_now(test_id):
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        v_run_id = cursor.callfunc(
            'TEST_PACKAGE.TEST_RUNNER',
            oracledb.NUMBER,
            [test_id]
        )

        if v_run_id is None:
            return {'success': False, 'error': 'Test is already running!'}

        connection.commit()
        cursor.close()

        return {'success': True, 'v_run_id': v_run_id}

    except oracledb.Error as error:
        app.logger.error("Failed to run test", exc_info=True)
        return {'success': False, 'error': 'A database error occurred.'}

@app.route('/run_test/<test_id>', methods=['POST'])
@login_required
def run_test(test_id):
    result = run_test_now(test_id)
    if result['success']:
        return jsonify({'success': True, 'message': 'Test started successfully!', 'v_run_id': result['v_run_id']})
    else:
        return jsonify({'success': False, 'error': result['error']}), 500

def schedule_test_run(test_id, start_time=None, recurrence=None):
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        repeat_interval = None
        if recurrence == "daily":
            repeat_interval = "FREQ=DAILY"
        elif recurrence == "weekly":
            repeat_interval = "FREQ=WEEKLY"
        elif recurrence == "monthly":
            repeat_interval = "FREQ=MONTHLY"

        p_start_date = None
        if start_time:
            p_start_date = datetime.fromisoformat(start_time)

        cursor.callproc(
            'TEST_PACKAGE.TEST_SCHEDULER',
            [test_id, p_start_date, repeat_interval, current_user.username]
        )

        connection.commit()
        cursor.close()
        return {'success': True}

    except oracledb.Error as error:
        app.logger.error("Failed to schedule test", exc_info=True)
        return {'success': False, 'error': 'A database error occurred.'}

@app.route('/schedule_test/<test_id>', methods=['POST'])
@login_required
def schedule_test_route(test_id):
    data = request.get_json(silent=True) or {}
    start_time = data.get("start_time")
    recurrence = data.get("recurrence")
    
    if not start_time:
        return jsonify({'success': False, 'error': 'Start time required'}), 400
    
    dt = datetime.fromisoformat(start_time)
    
    if dt <= datetime.now():
        return jsonify({'success': False, 'error': 'Start time must be in the future'}), 400


    result = schedule_test_run(test_id, start_time=start_time, recurrence=recurrence)
    if result['success']:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': result['error']}), 500


@app.route('/scheduled_jobs/<test_id>')
@login_required
def scheduled_jobs(test_id):
    cursor = pool.acquire().cursor()
    cursor.execute("""
        SELECT job_name, start_time, repeat_interval
        FROM SCHEDULED_TEST_RUNS
        WHERE test_id = :test_id AND active='Y'
        ORDER BY start_time
    """, {'test_id': test_id})
    rows = cursor.fetchall()

    # convert tuples to dicts
    jobs = []
    for row in rows:
        job_name, start_time, repeat_interval = row
        jobs.append({
            'job_name': job_name,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M') if start_time else None,
            'repeat_interval': repeat_interval
        })

    return jsonify(jobs)


@app.route('/delete_scheduled_run/<job_name>', methods=['POST'])
@login_required
def delete_scheduled_run(job_name):
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        cursor.execute("BEGIN DBMS_SCHEDULER.DROP_JOB(:job_name); END;", {'job_name': job_name})

        cursor.execute("""
            UPDATE SCHEDULED_TEST_RUNS
            SET active = 'N'
            WHERE job_name = :job_name
        """, {'job_name': job_name})

        connection.commit()
        cursor.close()
        return jsonify({'success': True})
    except oracledb.Error as e:
        app.logger.error("Failed to delete scheduled run", exc_info=True)
        return jsonify({'success': False, 'error': 'A database error occurred.'}), 500


@app.route('/archive_test', methods=['POST'])
@login_required
def archive_test():
    try:
        test_id = request.form['id']
        connection = pool.acquire()
        cursor = connection.cursor()

        cursor.execute("SELECT OWNER FROM TESTS WHERE ID = :id", {'id': test_id})
        owner_row = cursor.fetchone()

        if owner_row:
            owner = owner_row[0]
            if owner != current_user.username and not current_user.is_admin:
                return "Error: you are not the owner of this test plan.", 403
            
            cursor.execute("UPDATE TESTS SET ARCHIVED = 'YES' WHERE ID = :id", {'id': test_id})
            connection.commit()
        else:
            return "Error: Test not found.", 404

        cursor.close()
        return redirect(url_for('index'))

    except oracledb.Error as error:
        app.logger.error("Failed to archive test", exc_info=True)
        return "A database error occurred.", 500


@app.route('/kill_job', methods=['POST'])
@login_required
def kill_job():
    try:
        data = request.get_json()
        step_id = data.get('step_id')

        if not step_id:
            return jsonify({'message': 'Missing step ID'}), 400

        connection = pool.acquire()
        cursor = connection.cursor()

        query = """
            SELECT JOBNAME
            FROM STEP_RUN_LOG
            WHERE STEP_ID = :step_id
            ORDER BY EVENT_TIME DESC
            FETCH FIRST 1 ROWS ONLY
        """
        cursor.execute(query, {'step_id': step_id})
        row = cursor.fetchone()

        if not row:
            cursor.close()
            return jsonify({'message': f'No running job found for step {step_id}.'}), 404

        job_name = row[0]

        stop_query = "BEGIN DBMS_SCHEDULER.stop_job(JOB_NAME => :job_name); END;"
        cursor.execute(stop_query, {'job_name': job_name})

        connection.commit()
        cursor.close()

        return jsonify({'message': f'Job "{job_name}" stopped successfully.'})

    except oracledb.Error as error:
        app.logger.error("Failed to stop job", exc_info=True)
        return jsonify({'message': 'A database error occurred.'}), 500


@app.route('/test_steps_logs/<int:test_id>')
@login_required
def test_steps_logs(test_id):
    try:
        connection = pool.acquire()
        cursor = connection.cursor()

        query = """
            SELECT l.RUN_ID,
                   l.STEP_ID,
                   s.NAME AS STEP_NAME,
                   l.EVENT,
                   l.EVENT_TIME,
                   l.OUTPUT_MESSAGE,
                   l.ERROR_MESSAGE,
                   l.JOBNAME
            FROM STEP_RUN_LOG l
            JOIN TEST_STEPS s ON l.STEP_ID = s.ID
            WHERE s.TEST_ID = :test_id
            ORDER BY l.EVENT_TIME DESC
        """
        cursor.execute(query, {'test_id': test_id})

        logs = []
        columns = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            logs.append(dict(zip(columns, row)))

        cursor.close()
        connection.close()

        return render_template('test_steps_logs.html', test_id=test_id, logs=logs)

    except oracledb.Error as error:
        app.logger.error("Failed to load test logs", exc_info=True)
        return "A database error occurred.", 500




if __name__ == '__main__':
    app.run(debug=True)

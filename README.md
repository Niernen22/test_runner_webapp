About this Project:
This webapplication's goal is to allow users to copy tables from the production database and create+run test plans in the test database. The application generates the codes, only from the allowed types and data.
Made for oracle databases.

- Login required for viewing every page
  - Add User: create and delete users (alternatively, there's script for both of these functions to run in the terminal independently without login: create_user.py, delete_user.py)
  - Users: Listing all users, showing admin prviliges
    ONLY ADMINS can add or delete users on the page and see these buttons. Unpriviliged users can see the user list if they copy the url, but not the functions.
-Password change is available under 'Account'
- Main Page: Jobs and their statuses
- Test Steps for Test ID [..]: Test job's steps
- Edit Steps: Delete and Add steps for a job (ID, Test ID, Step Name, Order Number, Type, SQL Code, Target User
  - Add SQL: Select Step Type:
    - Table Copy (see OracleTableCopy repository): SELECT Source Schema, Source Table, Target Schema, Target Table, Truncate (true/false), Date; 
      Button Generate SQL e.g.: BEGIN TABLECOPY_PACKAGE.TABLECOPY('SARTASNADI', 'FORRAS_TABLA', 'SARTASNADI', 'CEL_TABLA', 'true', TO_DATE('2024-01-02','yyyy-mm-dd')); END;
    - LM Job: SELECT Module (-> Type spawns), Select Name
      Button Generate SQL e.g.: declare p_result varchar2(4000); p_err_code varchar2(4000); p_output clob; begin lm.undefined.execute(1, 'ODS#LM_INPUT_MEPO#E#MEPO', 'STAGE.MEPO_SERVICE_PRODUCT', p_result, p_err_code,                                       p_output, false); dbms_output.put_line(p_result || ' - ' || p_err_code); dbms_output.put_line(p_output); end; 
    - Stored Procedure: Stored Procedure Type:
      - Function or Procedure: Select Schema, Stored Function or Procedure Name, INPUT parameters into the generated textboxes
        Button Generate SQL e.g.: BEGIN SARTASNADI.TABLE_EXISTS(SARTASNADI, FORRAS_TABLA, SARTASNADI, CEL_TABLA); END;
      - Package: Select Schema, Stored Package Name, Stored Package's Function or Procedure Name, INPUT parameters into the generated textboxes
        Button Generate SQL e.g.: BEGIN TEST_RUNNER_REPO.TABLECOPY_PACKAGE.TABLE_EXISTS(SARTASNADI, FORRAS_TABLA); END;
    - (commented out at the moment) Truncate Table: Select Truncate Schema, Truncate Table, Date;
      Button Generate SQL e.g.: BEGIN TEST_RUNNER_REPO.TRUNCATE_TND_TABLE(A10LASZLO, TEST_TABLE, TO_DATE('2024-12-02','yyyy-mm-dd')); END;
  Button Submit: Adds the Job Type and SQL Code to the editing page
- Logs: The logs of the steps belonging to the test (Run ID, Step ID, Step Name, Event, Event Time, Output Message, Error Message, Job Name)

App design:
![login](https://github.com/user-attachments/assets/3aaab1d8-2008-493a-95d8-759e03529f13)
![index](https://github.com/user-attachments/assets/18e5d83b-29f3-4bee-b851-8ca6bc678d22)
![manage_users](https://github.com/user-attachments/assets/8f34d374-a253-4364-b1ae-158188ba9097)
![add_user](https://github.com/user-attachments/assets/39cd0346-e06c-4580-95f7-0e0d1016668e)
![delete_user](https://github.com/user-attachments/assets/fd087ce4-9dc2-4428-bdca-4ae50c1f8051)
![test_steps](https://github.com/user-attachments/assets/3b6cc62b-7c6e-4edf-a6cd-c9bef8b5a862)
![edit_steps](https://github.com/user-attachments/assets/275d1879-5c48-4fff-a8fc-f35d24824713)
![add_step_package](https://github.com/user-attachments/assets/66238c90-a65d-4af2-b25e-a1a87d2bc2eb)
![add_step_funcproc_pack](https://github.com/user-attachments/assets/2511fdd8-c52d-4938-ab1e-c9e50c527a98)
![add_step_funcproc](https://github.com/user-attachments/assets/84ad80fd-bfb5-4e64-90bb-6f579c283a01)
![add_step_lm](https://github.com/user-attachments/assets/aa63ad2c-4232-43ef-b22d-e1be173aa239)
![add_step_tablecopy](https://github.com/user-attachments/assets/0c5f396b-fcc3-4aa8-beb0-6f388e01332d)
![add_step_truncate](https://github.com/user-attachments/assets/59e334a0-4891-4e40-8651-18d67f4d2c4d)
![notice_of_adding](https://github.com/user-attachments/assets/a3eda36d-c974-4af2-b793-1395f2d6479c)
![edit_steps_order](https://github.com/user-attachments/assets/49f23b83-a55a-4690-b13a-f9eff62dc586)
![run_test](https://github.com/user-attachments/assets/8bc06e9f-e531-4c2f-9698-3a8b3834e466)


Tablecopy package:
Copying a partitioned table from one Oracle database into an other.

Checks if tables exist in actual db (targer table's) and in ODSD (source table's, db link can be replaced if other needed). Checks if tables have columns in common. Copies a range/list partitioned table, partitioned by date/number datatype column. If tablespace(s) and/or partition(s) are missing, creates them before datacopy. Copies full table or TND filtered, if truncate is TRUE, truncates target table's fully or only TND filtered part before.

Parameters

p_FORRAS_SEMA VARCHAR2 -- source table schema

p_FORRAS_TABLA VARCHAR2 -- source table name

p_CEL_SEMA VARCHAR2 -- target table schema

p_CEL_TABLA VARCHAR2 -- target table name

p_TRUNCATE BOOLEAN DEFAULT FALSE -- truncate target table TRUE/FALSE

p_TND_SZURES DATE DEFAULT NULL -- TND filter (Choosen date / Max date from source table / Current date of test database)


tables: 
-- Create table
create table TESTS
(
  id         NUMBER(22) not null,
  name       VARCHAR2(200 CHAR),
  status     VARCHAR2(10 CHAR),
  start_time TIMESTAMP(6),
  end_time   TIMESTAMP(6),
  run_id     NUMBER,
  archived   VARCHAR2(8),
  owner      VARCHAR2(20)
)
tablespace TEST_RUNNER_REPO
  pctfree 10
  initrans 1
  maxtrans 255
  storage
  (
    initial 80K
    next 1M
    minextents 1
    maxextents unlimited
  );
-- Create/Recreate primary, unique and foreign key constraints 
alter table TESTS
  add primary key (ID)
  using index
  tablespace TEST_RUNNER_REPO
  pctfree 10
  initrans 2
  maxtrans 255
  storage
  (
    initial 64K
    next 1M
    minextents 1
    maxextents unlimited
  );

-- Create table
create table TEST_STEPS
(
  id          NUMBER(22) not null,
  test_id     NUMBER(22),
  name        VARCHAR2(200 CHAR) not null,
  ordernumber NUMBER(22) not null,
  status      VARCHAR2(10 CHAR) not null,
  start_time  TIMESTAMP(6),
  end_time    TIMESTAMP(6),
  type        VARCHAR2(16 CHAR),
  sql_code    CLOB not null,
  target_user VARCHAR2(255),
  activity    VARCHAR2(20)
)
tablespace TEST_RUNNER_REPO
  pctfree 10
  initrans 1
  maxtrans 255
  storage
  (
    initial 80K
    next 1M
    minextents 1
    maxextents unlimited
  );
-- Create/Recreate indexes 
create index IND_TEST_STEPS on TEST_STEPS (TEST_ID)
  tablespace TEST_RUNNER_REPO
  pctfree 10
  initrans 2
  maxtrans 255
  storage
  (
    initial 80K
    next 1M
    minextents 1
    maxextents unlimited
  );
-- Create/Recreate primary, unique and foreign key constraints 
alter table TEST_STEPS
  add primary key (ID)
  using index
  tablespace TEST_RUNNER_REPO
  pctfree 10
  initrans 2
  maxtrans 255
  storage
  (
    initial 80K
    next 1M
    minextents 1
    maxextents unlimited
  );

-- Create table
create table TEST_RUN_LOG
(
  run_id        NUMBER,
  test_id       NUMBER,
  test_name     VARCHAR2(200),
  event         VARCHAR2(20),
  event_time    DATE,
  error_message CLOB
)
tablespace TEST_RUNNER_REPO
  pctfree 10
  initrans 1
  maxtrans 255
  storage
  (
    initial 80K
    next 1M
    minextents 1
    maxextents unlimited
  );

-- Create table
create table STEP_RUN_LOG
(
  run_id         NUMBER(22),
  step_id        NUMBER(22),
  step_name      VARCHAR2(200 CHAR),
  event          VARCHAR2(20),
  event_time     TIMESTAMP(6),
  output_message CLOB,
  error_message  CLOB,
  jobname        VARCHAR2(400 CHAR)
)
tablespace TEST_RUNNER_REPO
  pctfree 10
  initrans 1
  maxtrans 255
  storage
  (
    initial 80K
    next 1M
    minextents 1
    maxextents unlimited
  );

-- Create table
create table SCHEDULED_TEST_RUNS
(
  id              NUMBER(22) not null,
  test_id         NUMBER(22) not null,
  job_name        VARCHAR2(100),
  start_time      TIMESTAMP(6),
  repeat_interval VARCHAR2(200),
  created_at      TIMESTAMP(6) default SYSTIMESTAMP,
  created_by      VARCHAR2(20),
  active          VARCHAR2(1) default 'Y'
)
tablespace TEST_RUNNER_REPO
  pctfree 10
  initrans 1
  maxtrans 255
  storage
  (
    initial 80K
    next 1M
    minextents 1
    maxextents unlimited
  );
-- Create/Recreate primary, unique and foreign key constraints 
alter table SCHEDULED_TEST_RUNS
  add primary key (ID)
  using index
  tablespace TEST_RUNNER_REPO
  pctfree 10
  initrans 2
  maxtrans 255
  storage
  (
    initial 80K
    next 1M
    minextents 1
    maxextents unlimited
  );

-- Create table
create table USERS
(
  id       NUMBER generated by default as identity (start with 27),
  username VARCHAR2(50) not null,
  password VARCHAR2(255) not null,
  is_admin NUMBER(1) default 0
)
tablespace TEST_RUNNER_REPO
  pctfree 10
  initrans 1
  maxtrans 255
  storage
  (
    initial 80K
    next 1M
    minextents 1
    maxextents unlimited
  );
-- Create/Recreate primary, unique and foreign key constraints 
alter table USERS
  add primary key (ID)
  using index
  tablespace TEST_RUNNER_REPO
  pctfree 10
  initrans 2
  maxtrans 255
  storage
  (
    initial 80K
    next 1M
    minextents 1
    maxextents unlimited
  );
alter table USERS
  add unique (USERNAME)
  using index
  tablespace TEST_RUNNER_REPO
  pctfree 10
  initrans 2
  maxtrans 255
  storage
  (
    initial 80K
    next 1M
    minextents 1
    maxextents unlimited
  );



How to use this Project:
From your terminal, download the files using

$ git clone https://github.com/Niernen22/test_runner_webapp.git

Install all dependencies from the requirements.txt file.

$ pip install -r requirements.txt

Overwrite/Add config.py to add your credentials for the test database (Oracle database username, password, dns) in this format:
username = 'test_runner_username'
password = 'password'
dsn='dsn'
secret_key='secret_key'

Run the main.py file

$ python3 main.py

Type in http://localhost:5000 into your browser to view the project live. Type in CTRL-C to stop running the server.

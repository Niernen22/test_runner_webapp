# ODS Test Runner

A Flask web application for managing and running test plans against an Oracle database. Users can copy tables from production, build test steps with auto-generated SQL, run or schedule tests, and monitor results — all from a browser.

---

## Features

- **Test management** — create, run, schedule, archive, and kill tests
- **Step editor** — add, edit, duplicate, reorder, activate/deactivate, and delete steps per test
- **SQL generation** — auto-generates Oracle SQL from form inputs for supported step types
- **Logs** — full execution log per test run with output and error messages
- **Admin panel** — lists all failed steps across all tests with the test link, owner, and SQL that caused the error
- **User management** — admin-only user creation, deletion, and password management
- **Login required** for all pages

---

## Setup

### 1. Clone the repository
```
git clone https://github.com/Niernen22/test_runner_webapp.git
cd test_runner_webapp
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Configure credentials
Create a `config.py` file in the project root:
```python
username   = 'test_runner_repo'
password   = 'your_password'
dsn        = 'your_dsn'
secret_key = 'your_secret_key'
```

### 4. Set up the Oracle database
Run the table creation scripts from the [Database Schema](#database-schema) section below to create the required tables in your Oracle tablespace.

### 5. Create the first user
```
python create_user.py
```

### 6. Run the application
```
python main.py
```

Open `http://localhost:5000` in your browser. Press `CTRL+C` to stop the server.

---

## Pages

### Main Page `/`
Lists all tests with their name, status, owner, start/end times, and run ID. From here you can run, schedule, archive a test, or navigate to its steps.

### Test Steps `/test_steps/<test_id>`
Shows all steps belonging to a test with their order, type, status, and SQL code.

### Edit Steps `/edit_steps/<test_id>`
Full step editor for a test. Available actions per step:
- **Edit** — modify an existing step's name, type, SQL, order, or target user
- **Duplicate** — create a copy of a step
- **Activate / Deactivate** — toggle whether a step runs
- **Delete** — remove a step

Steps can be reordered by dragging. New steps are added via the **Add Step** button which opens a SQL generation form.

### Add Step — SQL Generation
Generates Oracle SQL based on the selected step type:

| Type | Generated SQL example |
|---|---|
| **Table Copy** | `BEGIN TABLECOPY_PACKAGE.TABLECOPY('SRC_SCHEMA', 'SRC_TABLE', 'TGT_SCHEMA', 'TGT_TABLE', 'true', TO_DATE('2024-01-02','yyyy-mm-dd')); END;` |
| **LM Job** | `begin lm.module.execute(1, 'ODS#LM_INPUT_MEPO#E#MEPO', 'STAGE.MEPO', p_result, p_err_code, p_output, false); end;` |
| **Stored Procedure / Function** | `BEGIN SCHEMA.PROCEDURE_NAME(param1, param2); END;` |
| **Package** | `BEGIN SCHEMA.PACKAGE_NAME.PROCEDURE_NAME(param1); END;` |

### Logs `/test_steps_logs/<test_id>`
Full execution log for a test run: Run ID, Step ID, Step Name, Event, Event Time, Output Message, Error Message, Job Name.

### Admin `/admin`
Lists all **failed** step log entries across every test, with:
- Link to the test
- Owner
- Step name and event time
- Error message, output message
- SQL that caused the failure

Paginated for large result sets.

### User Management `/manage_users`
Admin-only. Lists all users with their admin status. Admins can add or delete users and reset passwords. Non-admin users can see the list but not the action buttons.

### Account `/account`
Any logged-in user can change their own password here.

---

## User Management Scripts
These can be run directly from the terminal without logging in:

```
python create_user.py    # create a new user
python delete_user.py    # delete a user
python alter_user.py     # modify a user
```

---

## Database Schema

<details>
<summary>Click to expand table definitions</summary>

```sql
-- Tests
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
) tablespace TEST_RUNNER_REPO;
alter table TESTS add primary key (ID);

-- Test Steps
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
  activity    VARCHAR2(20),
  step_params CLOB
) tablespace TEST_RUNNER_REPO;
create index IND_TEST_STEPS on TEST_STEPS (TEST_ID);
alter table TEST_STEPS add primary key (ID);

-- Test Run Log
create table TEST_RUN_LOG
(
  run_id        NUMBER,
  test_id       NUMBER,
  test_name     VARCHAR2(200),
  event         VARCHAR2(20),
  event_time    DATE,
  error_message CLOB
) tablespace TEST_RUNNER_REPO;

-- Step Run Log
create table STEP_RUN_LOG
(
  run_id         NUMBER(22),
  step_id        NUMBER(22),
  step_name      VARCHAR2(200 CHAR),
  event          VARCHAR2(20),
  event_time     TIMESTAMP(6),
  output_message CLOB,
  error_message  CLOB,
  jobname        VARCHAR2(400 CHAR),
  step_sql       CLOB
) tablespace TEST_RUNNER_REPO;

-- Scheduled Test Runs
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
) tablespace TEST_RUNNER_REPO;
alter table SCHEDULED_TEST_RUNS add primary key (ID);

-- Users
create table USERS
(
  id       NUMBER generated by default as identity (start with 27),
  username VARCHAR2(50) not null,
  password VARCHAR2(255) not null,
  is_admin NUMBER(1) default 0
) tablespace TEST_RUNNER_REPO;
alter table USERS add primary key (ID);
alter table USERS add unique (USERNAME);
```

</details>

---

## App Screenshots

| | |
|---|---|
| ![login](https://github.com/user-attachments/assets/3aaab1d8-2008-493a-95d8-759e03529f13) | ![index](https://github.com/user-attachments/assets/18e5d83b-29f3-4bee-b851-8ca6bc678d22) |
| ![manage_users](https://github.com/user-attachments/assets/8f34d374-a253-4364-b1ae-158188ba9097) | ![add_user](https://github.com/user-attachments/assets/39cd0346-e06c-4580-95f7-0e0d1016668e) |
| ![test_steps](https://github.com/user-attachments/assets/3b6cc62b-7c6e-4edf-a6cd-c9bef8b5a862) | ![edit_steps](https://github.com/user-attachments/assets/275d1879-5c48-4fff-a8fc-f35d24824713) |
| ![add_step_tablecopy](https://github.com/user-attachments/assets/0c5f396b-fcc3-4aa8-beb0-6f388e01332d) | ![add_step_lm](https://github.com/user-attachments/assets/aa63ad2c-4232-43ef-b22d-e1be173aa239) |
| ![add_step_funcproc](https://github.com/user-attachments/assets/84ad80fd-bfb5-4e64-90bb-6f579c283a01) | ![add_step_package](https://github.com/user-attachments/assets/66238c90-a65d-4af2-b25e-a1a87d2bc2eb) |
| ![run_test](https://github.com/user-attachments/assets/8bc06e9f-e531-4c2f-9698-3a8b3834e466) | ![edit_steps_order](https://github.com/user-attachments/assets/49f23b83-a55a-4690-b13a-f9eff62dc586) |

---

## Tablecopy Package

The Table Copy step type uses the `TABLECOPY_PACKAGE` Oracle package. It copies a partitioned table from the production database into the test database.

**What it does:**
- Checks if source and target tables exist
- Verifies that source and target tables share common columns
- Handles range/list partitioned tables (partitioned by date or number)
- Creates missing tablespaces and/or partitions before copying
- Optionally truncates the target table (full or TND-filtered) before copying

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `p_FORRAS_SEMA` | VARCHAR2 | Source table schema |
| `p_FORRAS_TABLA` | VARCHAR2 | Source table name |
| `p_CEL_SEMA` | VARCHAR2 | Target table schema |
| `p_CEL_TABLA` | VARCHAR2 | Target table name |
| `p_TRUNCATE` | BOOLEAN | Truncate target before copy (default: FALSE) |
| `p_TND_SZURES` | DATE | TND filter date (default: NULL) |

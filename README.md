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
| ![login](docs/screenshots/login.png) | ![index](docs/screenshots/index.png) |
| ![manage_users](docs/screenshots/manage_users.png) | ![add_user](docs/screenshots/add_user.png) |
| ![new_password](docs/screenshots/new_password.png) | ![add_test](docs/screenshots/add_test.png) |
| ![add_step](docs/screenshots/add_step.png) | ![choose_stored_type](docs/screenshots/choose_stored_type.png) |
| ![add_stored_proc](docs/screenshots/add_stored_proc.png) | ![add_tablecopy_step](docs/screenshots/add_tablecopy_step.png) |
| ![add_lm](docs/screenshots/add_lm.png) | ![edit_steps](docs/screenshots/edit_steps.png) |
| ![run](docs/screenshots/run.png) | ![kill](docs/screenshots/kill.png) |
| ![kill_popup](docs/screenshots/kill_popup.png) | ![schedule_run](docs/screenshots/schedule_run.png) |
| ![view_logs](docs/screenshots/view_logs.png) | ![error_list](docs/screenshots/error_list.png) |
| ![archive](docs/screenshots/archive.png) | |

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

**Flow:**

```
TABLECOPY
  │
  ├─ SOURCE_EXISTS? ──NO──► RAISE ERROR
  ├─ TARGET_EXISTS? ──NO──► RAISE ERROR
  ├─ COMMON_COLUMNS? ──0──► RAISE ERROR
  │
  ├─ TND filter?
  │
  ├──NO──────────────────────────────────────────────────────┐
  │   ├─ Truncate? ──YES──► TRUNCATE whole target table      │
  │   ├─ RANGE_OR_LIST                                       │
  │   │     ├─ Both RANGE ──► create missing partitions      │
  │   │     ├─ Both LIST  ──► create missing partitions      │
  │   │     ├─ Mismatch   ──► RAISE ERROR                    │
  │   │     └─ Both NULL  ──► do nothing (not partitioned)   │
  │   └─ COPY_COLUMNS                                        │
  │         └─ INSERT SELECT [FETCH FIRST n]                 │
  │                                                          │
  └──YES─────────────────────────────────────────────────────┘
      ├─ Source has TND column? ──NO──► RAISE ERROR
      ├─ Target has TND column? ──NO──► RAISE ERROR
      ├─ Check if target's TND partition exists
      ├─ Truncate? ──YES──► TRUNCATE_TND_TABLE
      │
      ├─ TND partition exists?
      │
      ├──NO──► Target has any partitions?
      │             ├──YES──► RANGE_OR_LIST_TND (create TND partition)
      │             │              └─► COPY_COLUMNS_TND (INSERT WHERE TND=date [FETCH FIRST n])
      │             └──NO───► COPY_COLUMNS_TND (INSERT WHERE TND=date [FETCH FIRST n])
      │
      └──YES──► COPY_COLUMNS_TND (INSERT WHERE TND=date [FETCH FIRST n])
      │
      └─ COMMIT
      └─ Target = STAGE? ──YES──► set_stage_data_last_tnd
```

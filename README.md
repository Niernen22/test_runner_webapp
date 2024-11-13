About this Project:
This is a webapplication in the process, the goal is to let developers make their own test plans and run them independently from system administrators.
Made for oracle databases.

At the moment the following is available:
- Login required for viewing every page
  - Add User: create and delete users (alternatively, there's script for both of these functions to run in the terminal independently without login: create_user.py, delete_user.py)
  - Users: Listing all users, showing admin prviliges
    ONLY ADMINS can add or delete users on the page and see these buttons. Unpriviliged users can see the user list if they copy the url, but not the functions.
- Main Page: Jobs and their statuses
- Test Steps for Test ID [..]: Test job's steps
- Edit Steps: Delete and Add steps for a job (ID, Test ID, Step Name, Order Number, Type, SQL Code, Target User
  - Add SQL: Select Step Type:
    - Table Copy (see OracleTableCopy repository): SELECT Source Schema, Source Table, Target Schema, Target Table, Truncate (true/false), Date; 
      Button Generate SQL e.g.: BEGIN TABLECOPY_PACKAGE.TABLECOPY('SARTASNADI', 'FORRAS_TABLA', 'SARTASNADI', 'CEL_TABLA', 'true', TO_DATE('2023-01-02','yyyy-mm-dd')); END;
    - LM Job: SELECT Module (-> Type spawns), Select Name
      Button Generate SQL e.g.: declare p_result varchar2(4000); p_err_code varchar2(4000); p_output clob; begin lm.undefined.execute(1, 'ODS#LM_INPUT_MEPO#E#MEPO', 'STAGE.MEPO_SERVICE_PRODUCT', p_result, p_err_code,                                       p_output, false); dbms_output.put_line(p_result || ' - ' || p_err_code); dbms_output.put_line(p_output); end; 
    - Stored Procedure: Stored Procedure Type:
      - Function or Procedure: Select Schema, Stored Function or Procedure Name, INPUT parameters into the generated textboxes
        Button Generate SQL e.g.: BEGIN SARTASNADI.TABLE_EXISTS(SARTASNADI, FORRAS_TABLA, SARTASNADI, CEL_TABLA); END;
      - Package: Select Schema, Stored Package Name, Stored Package's Function or Procedure Name, INPUT parameters into the generated textboxes
        Button Generate SQL e.g.: BEGIN SARTASNADI.TABLECOPY_PACKAGE.TABLE_EXISTS(SARTASNADI, FORRAS_TABLA); END;
  Button Submit: Adds the Job Type and SQL Code to the editing page
- Job Log Details: Job logging (Run ID, Test ID, Test Name, Event, Event Time, Error Message)
- Job Steps Log Details: Job Steps Logging (Run ID, Step ID, Step Name, Event, Event Time, Output Message, Error Message, Job Name)

App design:
![login](https://github.com/user-attachments/assets/358410dc-1e06-40f8-bf8f-c36cd4863725)
![index](https://github.com/user-attachments/assets/25eba555-7ff0-4e6c-8a78-f94e13540efe)
![job_steps_details](https://github.com/user-attachments/assets/6b4f6d08-d731-40bb-8f45-117794035d0c)
![edit_steps](https://github.com/user-attachments/assets/be17c308-bbca-43a1-9b21-bdf3f4165e18)

Tablecopy package:
Copying a partitioned table from one Oracle database into an other.

Checks if tables exist in actual db (targer table's) and in ODSD (source table's, db link can be replaced if other needed). Checks if tables have columns in common. Copies a range/list partitioned table, partitioned by date/number datatype column. If tablespace(s) and/or partition(s) are missing, creates them before datacopy. Copies full table or TND filtered, if truncate is TRUE, truncates target table's fully or only TND filtered part before.

Parameters

p_FORRAS_SEMA VARCHAR2 -- source table schema

p_FORRAS_TABLA VARCHAR2 -- source table name

p_CEL_SEMA VARCHAR2 -- target table schema

p_CEL_TABLA VARCHAR2 -- target table name

p_TRUNCATE BOOLEAN DEFAULT FALSE -- truncate target table TRUE/FALSE

p_TND_SZURES DATE DEFAULT NULL -- TND filter


Runs and logs (output and error messages) a test's steps based on the test's ID (given as parameter).

tables: TESTS -- TEST_RUN_LOG TEST_STEPS -- STEP_RUN_LOG

how to call it in oracle db: DECLARE l_run_id NUMBER; BEGIN l_run_id := TEST_PACKAGE.TEST_RUNNER(234); -- Pass the desired v_id as an argument DBMS_OUTPUT.PUT_LINE('Run ID: ' || l_run_id); END; /



How to use this Project:
From your terminal, download the files using

$ git clone https://github.com/Niernen22/Job_steps_webapp.git

Install all dependencies from the requirements.txt file.

$ pip install -r requirements.txt

Open the config.py to add your credentials (Oracle database username, password, dns).

Run the main.py file

$ python3 main.py

Type in http://localhost:5000 into your browser to view the project live. Type in CTRL-C to stop running the server.

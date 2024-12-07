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
      Button Generate SQL e.g.: BEGIN TABLECOPY_PACKAGE.TABLECOPY('SARTASNADI', 'FORRAS_TABLA', 'SARTASNADI', 'CEL_TABLA', 'true', TO_DATE('2024-01-02','yyyy-mm-dd')); END;
    - LM Job: SELECT Module (-> Type spawns), Select Name
      Button Generate SQL e.g.: declare p_result varchar2(4000); p_err_code varchar2(4000); p_output clob; begin lm.undefined.execute(1, 'ODS#LM_INPUT_MEPO#E#MEPO', 'STAGE.MEPO_SERVICE_PRODUCT', p_result, p_err_code,                                       p_output, false); dbms_output.put_line(p_result || ' - ' || p_err_code); dbms_output.put_line(p_output); end; 
    - Stored Procedure: Stored Procedure Type:
      - Function or Procedure: Select Schema, Stored Function or Procedure Name, INPUT parameters into the generated textboxes
        Button Generate SQL e.g.: BEGIN SARTASNADI.TABLE_EXISTS(SARTASNADI, FORRAS_TABLA, SARTASNADI, CEL_TABLA); END;
      - Package: Select Schema, Stored Package Name, Stored Package's Function or Procedure Name, INPUT parameters into the generated textboxes
        Button Generate SQL e.g.: BEGIN TEST_RUNNER_REPO.TABLECOPY_PACKAGE.TABLE_EXISTS(SARTASNADI, FORRAS_TABLA); END;
    - Truncate Table: Select Truncate Schema, Truncate Table, Date;
      Button Generate SQL e.g.: BEGIN TEST_RUNNER_REPO.TRUNCATE_TND_TABLE(A10LASZLO, TEST_TABLE, TO_DATE('2024-12-02','yyyy-mm-dd')); END;
  Button Submit: Adds the Job Type and SQL Code to the editing page
- Job Log Details: Job logging (Run ID, Test ID, Test Name, Event, Event Time, Error Message)
- Job Steps Log Details: Job Steps Logging (Run ID, Step ID, Step Name, Event, Event Time, Output Message, Error Message, Job Name)

App design:
![login](https://github.com/user-attachments/assets/3aaab1d8-2008-493a-95d8-759e03529f13)
![index](https://github.com/user-attachments/assets/18e5d83b-29f3-4bee-b851-8ca6bc678d22)
![manage_users](https://github.com/user-attachments/assets/8f34d374-a253-4364-b1ae-158188ba9097)
![add_user](https://github.com/user-attachments/assets/39cd0346-e06c-4580-95f7-0e0d1016668e)
![delete_user](https://github.com/user-attachments/assets/fd087ce4-9dc2-4428-bdca-4ae50c1f8051)
![test_steps](https://github.com/user-attachments/assets/3b6cc62b-7c6e-4edf-a6cd-c9bef8b5a862)
![edit_steps](https://github.com/user-attachments/assets/275d1879-5c48-4fff-a8fc-f35d24824713)
![add_step_package](https://github.com/user-attachments/assets/082c2262-ec81-4749-8bbd-325b804d8766)
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

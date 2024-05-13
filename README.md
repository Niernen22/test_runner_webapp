About this Project:
This is a webapplication in the process, the goal is to let developers make their own test plans and run them independently from system administrators.

At the moment the following is available:
- Main Page: Jobs and their statuses
- Test Steps for Test ID [..]: Test job's steps
- Edit Steps: Delete and Add steps for a job (ID, Test ID, Step Name, Order Number, Type, SQL Code, Target User
- Job Log Details: Job logging (Run ID, Test ID, Test Name, Event, Event Time, Error Message)
- Job Steps Log Details: Job Steps Logging (Run ID, Step ID, Step Name, Event, Event Time, Output Message, Error Message, Job Name)





How to use this Project:
From your terminal, download the files using

$ git clone https://github.com/Niernen22/Job_steps_webapp.git

Install all dependencies from the requirements.txt file.

$ pip install -r requirements.txt

Open the config.py to add your credentials to the Oracle database (username, password, dns).

Run the main.py file

$ python3 main.py

Type in http://localhost:5000 into your browser to view the project live. Type in CTRL-C to stop running the server.

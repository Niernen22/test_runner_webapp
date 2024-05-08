This is a webapplication in the process, the goal is to make the OracleTableCopy procedure easily accessable, usable and the running processes more seethrough.

At the moment it can: 
Connect to the Oracle database specified.
Show the jobs and their statuses (from the table specified in the config file).
Generate a link to show the belonging job steps (ID, Name, Ordernumber, Status, Start time, End time, Type, SQL code, Target user).

Join: 
Tests:ID = Test_steps:Test_ID

See more information about the procedure in the OracleTableCopy repository.


How to use this Project
From your terminal, download the files using

$ git clone https://github.com/Niernen22/Job_steps_webapp.git
A virtual environment is a tool that helps to keep dependencies required by different projects separate from each other by using isolated virtual environments. The venv module comes pre installed with Python 3.5 + versions. Create your virtual environment

$ python3 -m venv env
$ source env/bin/activate
I created the requirements.txt file using the pip freeze command. Install all dependencies from the requirements.txt file.

$ pip install -r requirements.txt
Run the main.py file

$ python3 main.py
Type in http://localhost:5000 into your browser to view the project live. Type in CTRL-C to stop running the server.

To deactivate your environment:

$ deactivate

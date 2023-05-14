# Text Summararization and Semantic Evaluation

## Steps to run the project on local

1. Download the project repository (If using VSCode, you can clone the repository in VSCode)

2. Open the repository in any IDE (VSCode recommended)

3. Make sure python and pip are installed \
    `$ python --version` \
    `$ pip --version` 

4. Install and create virtual environment in the repository. Virtual environment with python 3.8.3 is recommended. \
	`$ pip install virtualenv` \
	`$ virtualenv env` OR `$ virtualenv env --python=python3.8.3`

5. Activate the virtual Environment. On activation you can see (env) on left side of terminal. \
    Run this command for mac or linux OS: \
	`$ source env/bin/activate`  \
    Run this command for windows OS: \
    `$ env\Scripts\activate`

6. To installl all modules in Requirements File	\
	`$ pip install -r requirements.txt` 
   
   If this doesn't work, install these modules one by one: \
   `$ pip install flask` \
   `$ pip install flask_sqlalchemy` \
   `$ pip install flask_wtf` \
   `$ pip install flask_login` \
   `$ pip install flask_bcrypt` \
   `$ pip install transformers` \
   `$ pip install sentence_transformers` \
   `$ pip install torchmetrics`

7. After this run the app \
    `$ python app.py`

8. To stop the app press (cnrl + C). \
   To deactivate the virtual environment, run this command: \
    `$ deactivate`

# Text-Summary-Evaluation

## Steps to run the project on local

1. Download the project repository (If using VSCode, you can clone the repository in VSCode)

2. Open the repository in any IDE (VSCode preferred)

3. Make sure python and pip are installed \
    `$ python --version` \
    `$ pip --version` 

4. Install and create virtual environment in the repository \
	`$ pip install virtualenv` \
	`$ virtualenv env --python=python3.8.3` 

5. Activate the virtual Environment. On activation you can see (env) on left side of terminal. \
    Run this command for mac and linux: \
	`$ source env/bin/activate`  \
    Run this command for windows: \
    `$ env\Scripts\activate`

6. To installl all modules in Requirements File	\
	`$ pip install -r requirements.txt` \
   If anything fails to install, make sure that the virtual environment has python 3.8.3 version. 
   
   If modules are not installing through Requirements file then just run `$ python app.py` and install the suggested modules.

7. After this run the app \
    `$ python app.py`

8. Press (cnrl + C) to stop the app, and run this command to stop virtual environment \
    `$ deactivate`

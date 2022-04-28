# [Project RePhoto](https://rameme.pythonanywhere.com/)

[rePhoto](https://rameme.pythonanywhere.com/) is a website that makes this easier, so you (or a group!) can align and take many pictures of a place or an object. These pictures are a visual record of change -- pictures of trees or streams or beaches over time are useful to measure the effects of erosion and climate change; pictures of home improvement projects (or even yourself) can serve as a visual timeline of events.

## Preview

[![Current Site](https://github.com/Chen-Hao-Liu/flask_rephoto/blob/master/flaskr/static/imgs/screenCapture.png)](https://rameme.pythonanywhere.com/)

1. Create a new account on pythonanywhere.com. The free/beginner version is fine to start with.
2. Once you’ve created your account, go to the Consoles page and create a new bash console.
3. Git clone the rephoto repository from the following link: https://github.com/Project-rePhoto/rePhoto
4. Next, enter the rePhoto directory and run pip install -r --user requirements.txt. This will automatically install the requirements listed.
5. Click to the Web page and click Add a new web app. The beginners account won’t let you change your domain name, which is fine, you can do so later if you choose to upgrade your account.
6. Select a python web framework, click manual configuration.
7. Choose the latest python version (3.8 as of 1/14/2021)
8. Click next to finish
9. Click the green reload button and then click the domain link right above it. You should be met with a basic hello world html. Now you know your webapp was set up correctly.
10. Next go to the Code section and change source code to rePhoto:
11. /home/<username>/rePhoto (e.g. /home/PrePhoto/rePhoto)
12. Click into the wsgi config file. You can delete the section of the html and python script application(environ, start_response) that prints HELLO_WORLD. Go down to the flask section and uncomment/edit the code parts so that you are left with:

```
import sys
    path = '/home/<username>/rePhoto'
if path not in sys.path:
    sys.path.append(path)

from flaskr import create_app
application = create_app()
```
13. There’s still a few libraries left to import. We need to import these packages in our virtual environment, so delete the old bash console and under web, scroll down to virtualenv, and click on start a console in this virtualenv.
14. Within the console, install flask-mysql and Flask-Mail.
    * pip install --user flask-mysql
    * pip install --user Flask-Mail
17. To initialize a new database, click under databases, click MySQL and create a username/password. 
18. Under your databases, click on the default db link to start a console! Run the commands below:
  use <database name>
  source rePhoto/flaskr/schema.sql

19. Create a file called config.py under the flaskr directory. The contents are as following:

```
#MySQL database
username = '<username>'
password = '<password>'
database = '<username>$default'
host = '<username>.mysql.pythonanywhere-services.com'

#email confirmation
pass_salt = 'random_string_for_salt'
secret_key = 'random_secret_key'

#group email credentials
org_email = 'rephoto@gmail.com'
org_email_pass = 'somepass'
```

(Note: you will need to create an email for the org and put the credentials here in order to enable the email confirmation functionality.)

20. In order to setup the Vision API, refer to the following instructions:
  * https://codelabs.developers.google.com/codelabs/cloud-vision-api-python#2
  * create a service account, enable vision api/billing, and generate key
  * Store the key.json file under your user directory /home/<username>: (e.g. /home/PrePhoto)
  * Run pip3 install -U pip google-cloud-vision in virtualenv console
  * Check to see if correctly installed with python3 -c "import google.cloud.vision"

21. Afterwards, there are files under rePhoto/flaskr that still have the original rameme/directory as part of the path (rameme is another username). Find the location of these paths and replace with your own username. Also, under templates, check all the html files as well for ‘rameme’ and change everywhere to the new path.

22. Enable Force HTTPS under Security in the web app setup.

The page should be ready to go! Refresh the site and check it out.

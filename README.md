# Task Manager
#### Video Demo: https://www.youtube.com/watch?v=ZZMHx_vqP6I
#### Running:
Navigate to the code directory and execute the following commands
```
$ pip install -r requirements.txt
$ flask run
```
Then open a web browser and go to the link shown at "INFO:  * Running on _______"
#### Description:
Task Manager is my [CS50 Final Project.](https://cs50.harvard.edu/x/2022/project/) It is a Flask website to create, edit, and complete tasks, as well as compete with others. This project draws heavy influence from PSet9 (Finance) and PSet8 (Homepage). It uses HTML, CSS, Javascript, Flask, and Jinja to run. The structure is similar to PSet9, as it is Flask's standards. The project is simple in appearance but rich in quality-of-life features, security, and bug fixes.

The flask_session folder stores data about user sessions.
The static folder contains a .ico file (the little image next to the title on a webpage) and the website's stylesheet.
The templates folder contains several webpages, most of which inherit from layout.html. layout.html is similar to PSet9 as well but contains a few more details, like better implementations of flash messages.
data.db contains the site's database. The table "users" keeps track of the usernames and (hashed) passwords of all users on the site, as well as their completed task counts. The table "tasks" contains outstanding tasks, with a foreign key pointing to the user that created them.
README.md is this file, which contains the project's title, the video link, and the description (you are reading right now!).
requirements.txt stores all of the libraries used throughout the project.

helpers.py contains a few functions and decorations used throughout app.py.
"error" flashes a message as an error (red background) and redirects to the website the user is already on. Likewise, "success" flashes a message as a success (green background) and redirects to the index. These two functions are used in place of PSet9's apologies. This is better design because while the cat meme is hilarious, it is not practical because it forces the user to click back into the page that they were on, rather than already being there.
Similar to PSet9, the @login_required decoration makes sure the user is logged in before giving access to pages like index, create, edit, and leaderboard. If the user is not logged in, they are redirected to /login. However, due to a bug I found,
I also added the @login_blocked decoration, which makes sure the user is logged out before accessing /register or /login (which causes strange behavior if they are logged in), and if they are logged in, they are redirected to the index.

Finally, the bulk of the project, app.py.
The file starts with configurations just like those in PSet9, for example, ensuring that sessions are saved in a file system rather than cookies.
The after-response function makes sure that responses to forms are not cached after a request.
Then the rest of the file contains paths. Many of the paths are near identical to those in PSet9 (except for replacing the apology system with the flash system). I will skip the explanation of /login and /logout. The only thing that I changed in /login is that when an error occurs (like an incorrect password) when redirecting back to /login, the username is cached, and appears already typed in the box. As an extra quality-of-life feature, I also autofocused to the password box (instead of the username box) when the username was already typed.
/register is similar as well, but after making all other checks, it checks the length and contents of the password, making sure it is secure (criteria in the render template). If it is, the user can register. Also, the same caching system in /login applies here.
/leaderboard is GET only, it uses Jinja to make a table of users' names and task counts.
/create uses GET and POST. It also has similar caching of task titles (like if you accidentally forget to write a time). It has several checks to make sure a name exists, the date is in the correct format, etc. There are two buttons in the template, "create" and "create another". The name attribute of both buttons is set. The script can check both buttons by checking if the name attribute of a button is "in" request.form. If it is, that button has been clicked. This will cause the "create" button to redirect to index, while the "create another" button redirects back to /create.

The index is the most complicated route. Unlike the index in PSet9, it uses GET and POST.
On GET, the first thing it does is it checks for the key "tz" in the session. It is very important later. If the key does not exist, it returns the render template fetch_timezone.html. This render template is very unique. Unlike all others, who contain a few basic tasks and inherit layout.html, this template does not inherit. Its sole purpose is to solve my problem with time zones. After much experimentation, I realized that it is impossible to get the user's timezone server-side. I dug up the javascript that does the job. In the body, a single-purpose form exists, just to get data to app.py through POST. It contains a hidden number field, that by default is empty. After the page loads, javascript executes. It sets the value of the timezone to the number of minutes in difference between the current UTC time zone, and the user's local timezone. After that value is changed, the form is submitted via POST back to /fetch_timezone. This route stores the returned value in session["tz"] and returns to the index. After this value is finally found, the code can continue. The code first finds the current time in UTC. Then it finds the local time by subtracting that number session["tz"] in minutes from the current UTC time. Then it gets all of the tasks made by the active user and loops through them. The code adds a key to the task dictionary, "overdue", made by comparing the task's due date to the local time. After that key is added, GET is finally done and it can return the render template.
This render template is by far the most complex. If there are no tasks, the webpage simply says "You have no tasks!" and allows you to create one, rather than displaying an empty table. Otherwise, the template tells you your number of tasks (checked for plurality) as well as your overdue tasks, if any (checked for plurality as well). In the table, overdue tasks are marked by setting the background color of the date box to red. One design debate I made here was how to display the table. I decided on textboxes for the name, databoxes for the date, and radio buttons for complete and delete. I chose radio buttons, even though checkboxes might look better because I didn't want the user to be able to select both and cause confusion.
In the index's POST, it first checks if the create button was pressed (using a strategy similar to /create). Otherwise, it saves all changes. It counts any errors made in format and flashes an error for each. There is a lot of error checking, too much to explain here.

Finally the last route, edit. It uses GET, POST and two different render templates.
On the initial GET, if there is only 1 task, it skips a step and goes straight to the edit template. Otherwise, it returns a select template in which the user can select a task to edit (if no tasks exist, feedback similar to the index is presented). After select.html is submitted via POST, the website detects it (based on the button name) and loads edit.html. This website allows changes to the task, as well as completion and deletion. After that, it is submitted to /edit again via POST, the button is detected, and edits are saved (with similar error checking in /create).

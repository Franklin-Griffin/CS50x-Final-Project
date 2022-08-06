from datetime import datetime
from datetime import timedelta
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, login_blocked, error, success

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///data.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/fetch_timezone", methods=["POST"])
def fetch_timezone():
    session["tz"] = request.form.get("offset")
    return redirect("/")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        if not "tz" in session.keys():
            # Important later
            return render_template("fetch_timezone.html")

        # Get current time in UTC
        now = datetime.now()

        # Offset by user's timezone
        now -= timedelta(minutes=int(session["tz"]))

        tasks = db.execute("SELECT task_id, name, due FROM tasks WHERE user_id = ?", session["user_id"])

        count = 0
        # Add overdue marker
        for row in tasks:
            # Get due date
            duedate = row["due"]
            # Turn it to timestamp object
            duedate = duedate.replace("T", " ")
            dt = datetime.strptime(duedate, "%Y-%m-%d %H:%M")
            # Compare (returns boolean)
            overdue = now > dt
            # Add marker
            row["overdue"] = overdue
            if overdue:
                count += 1

        return render_template("index.html", tasks=tasks, overdue=count)

    # POST

    if "create" in request.form:
        # Redirect to create page
        return redirect("/create")

    taskstocheck = db.execute("SELECT task_id FROM tasks WHERE user_id = ?", session["user_id"])

    errors = 0

    for _task in taskstocheck:
        # Clean it up
        task = _task["task_id"]

        # Check hackers
        if request.form.get("nameof:"+str(task)) == None or request.form.get("dueof:"+str(task)) == None:
            flash("Hacking detected, changes to task of id " + str(task) + " not found. Updates will not save.", "error")
            errors += 1
        else:
            if request.form.get("deleteof:"+str(task)) != None:
                # Works for done or delete
                db.execute("DELETE FROM tasks WHERE task_id = ?", task)
                if request.form.get("deleteof:"+str(task)) == "done":
                    db.execute("UPDATE users SET tasks = tasks + 1 WHERE id = ?", session["user_id"])
                continue

            # Error checking and updates
            if not request.form.get("nameof:"+str(task)) == "":
                db.execute("UPDATE tasks SET name = ? WHERE task_id = ?", request.form.get("nameof:"+str(task)), task)
            else:
                flash("Missing name for task of id " + str(task), "error")
                errors += 1
            if not request.form.get("dueof:"+str(task)) == "":
                try:
                    datetime.strptime(request.form.get("dueof:"+str(task)).replace('T', ' '), "%Y-%m-%d %H:%M")
                except:
                    flash("Date in incorrect format for task of id " + str(task) +
                          ". Did you forget a time or enter five digits for a year?", "error")
                    errors += 1
                else:
                    db.execute("UPDATE tasks SET due = ? WHERE task_id = ?", request.form.get("dueof:"+str(task)), task)
            else:
                flash("Missing due date for task of id " + str(task), "error")
                errors += 1

    if errors == 0:
        return success("Changes successfully saved!")
    elif errors == 1:
        return error("Other changes saved with 1 error")
    else:
        return error("Other changes saved with " + str(errors) + " errors")


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if not "cache" in session.keys():
        session["cache"] = ""

    if request.method == "GET":
        return render_template("create.html", cache=session["cache"])

    name = request.form.get("name")
    due = request.form.get("due")
    session["cache"] = name

    if name == "":
        return error("Please name your task")
    if due == "":
        return error("Please set a due date for your task")
    try:
        datetime.strptime(due.replace('T', ' '), "%Y-%m-%d %H:%M")
    except:
        return error("Date is in incorrect format. Did you forget a time or enter five digits for a year?")
    else:
        # Everything is good
        db.execute("INSERT INTO tasks (user_id, name, due) VALUES (?, ?, ?)", session["user_id"], name, due)
        session["cache"] = ""
        if "cr" in request.form:
            # Override default success behaviour (redirecting to /create rather than /)
            flash("Task created!", "success")
            return redirect("/create")

        return success("Task created!")


@app.route("/leaderboard")
@login_required
def leaderboard():
    lb = db.execute("SELECT username, tasks, id FROM users ORDER BY tasks DESC")
    return render_template("leaderboard.html", lb=lb, me=session["user_id"])


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "GET":
        options = db.execute("SELECT name, task_id, due FROM tasks WHERE user_id = ?", session["user_id"])
        if len(options) == 1:
            # Only one option
            return render_template("edit.html", task=options[0], back=False)
        return render_template("select.html", options=options)

    if "create" in request.form:
        # User had no tasks and clicked button
        return redirect("/create")

    if "select" in request.form:
        # Reached this page via select.html
        task = db.execute("SELECT name, task_id, due FROM tasks WHERE task_id = ?", request.form.get("task"))[0]
        return render_template("edit.html", task=task, back=True)

    # Reached this page via edit.html
    if "back" in request.form:
        return redirect("/edit")

    task = request.form.get("id")
    # Check hackers
    x = db.execute("SELECT user_id FROM tasks WHERE task_id = ?", task)
    if len(x) == 0 or x[0]["user_id"] != session["user_id"]:
        return error("You thought you could hack this site? Guess again.")

    if "delete" in request.form:
        db.execute("DELETE FROM tasks WHERE task_id = ?", task)
        return success("Task deleted!")

    if "complete" in request.form:
        db.execute("UPDATE users SET tasks = tasks + 1 WHERE id = ?", session["user_id"])
        db.execute("DELETE FROM tasks WHERE task_id = ?", task)
        return success("Task marked as done!")

    # if "save" in request.form:
    name = request.form.get("name")
    due = request.form.get("due")
    # Error checking and updates
    if name == "":
        return error("Please name your task")
    if due == "":
        return error("Please set a due date for your task")
    try:
        datetime.strptime(due.replace('T', ' '), "%Y-%m-%d %H:%M")
    except:
        return error("Date is in incorrect format. Did you forget a time or enter five digits for a year?")
    else:
        # Everything is good
        db.execute("UPDATE tasks SET name = ?, due = ? WHERE task_id = ?", name, due, task)
        return success("Task edited!")


@app.route("/register", methods=["GET", "POST"])
@login_blocked
def register():
    if not "cache" in session.keys():
        session["cache"] = ""

    if request.method == "GET":
        return render_template("register.html", cache=session["cache"])

    username = request.form.get("username")
    password = request.form.get("password")
    confirm = request.form.get("confirmation")

    if not username or username == "":
        session["cache"] = ""
        return error("Please enter a name")

    session["cache"] = username

    if len(db.execute("SELECT * FROM users WHERE username = ?", username)) != 0:
        return error("Username already exists. Are you trying to <a href='/login'>log in?</a>")
    if not password or password == "":
        return error("Please enter a password")
    if not confirm or confirm == "":
        return error("Please enter a confirmation password")
    if not password == confirm:
        return error("Passwords do not match")
    # Passwords must have 8 characters, a number, a letter, and a special character
    if len(password) < 8:
        return error("Your password is not long enough")
    number = False
    letter = False
    special = False
    for i in password:
        if i.isnumeric():
            number = True
        elif i.isalpha():
            letter = True
        else:
            # Special character
            special = True
    if not number:
        return error("Your password must contain a number")
    if not letter:
        return error("Your password must contain a letter")
    if not special:
        return error("Your password must contain a special character")
    # Register user and log in
    db.execute("INSERT INTO users (username, hash, tasks) VALUES (?, ?, 0)", username, generate_password_hash(password))
    session["user_id"] = db.execute("SELECT * FROM users WHERE username = ?", username)[0]["id"]
    session["user_name"] = username
    session["cache"] = ""
    return success("You have successfully registered!")


@app.route("/login", methods=["GET", "POST"])
@login_blocked
def login():
    if not "cache" in session.keys():
        session["cache"] = ""

    if request.method == "GET":
        return render_template("login.html", cache=session["cache"])

    # POST
    if not request.form.get("username"):
        session["cache"] = ""
        return error("You must provide a username")

    session["cache"] = request.form.get("username")

    if not request.form.get("password"):
        return error("You must provide a password")
    rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
    if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
        return error("Invalid username and/or password")
    session["user_id"] = rows[0]["id"]
    session["user_name"] = db.execute("SELECT username FROM users WHERE id = ?", rows[0]["id"])[0]["username"]
    session["cache"] = ""
    return success("You are now logged in!")


@app.route("/logout")
def logout():
    session.clear()
    return success("You have successfully been logged out!")
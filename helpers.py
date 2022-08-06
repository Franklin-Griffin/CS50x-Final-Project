from flask import redirect, flash, request, session
from functools import wraps


def error(message):
    # A function that displays a red message at the top of the page when loaded
    flash(message, "error")
    return redirect(request.path)


def success(message):
    # A function that displays a green message at the top of the page when loaded
    flash(message, "success")
    return redirect("/")


def login_required(f):
    # A function that forces the user from viewing pages that require a login

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def login_blocked(f):
    # A function that blocks the user from viewing routes like login or register (and causing strange behavior) until they are logged out

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (session.get("user_id") is None):
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function
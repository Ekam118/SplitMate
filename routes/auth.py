from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

from extensions import db
from models import User

auth = Blueprint("auth", __name__)


@auth.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard_home"))
    return redirect(url_for("auth.login"))

# -------------------------------------------------------------------------REGISTER---------------------------------------------------------------
@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"].strip()
        username = request.form["username"].strip().lower()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if not fullname or not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.register"))
        
        # Password Strength Validation
        # if len(password) < 8:
        #     flash("Password must be at least 8 characters long.","danger")
        #     return redirect(url_for("auth.register"))
        
        existing_user = User.query.filter(or_(User.username == username,User.email == email)).first()
        

        if existing_user:
            flash("Username or Email already exists.", "danger")
            return redirect(url_for("auth.register"))

        new_user = User(
            fullname=fullname,
            username=username,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        login = request.form["login"].strip().lower()
        password = request.form["password"]
        user = User.query.filter(or_(User.username == login,User.email == login)).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id
            # session["username"] = user.username

            flash("Login successful.", "success")
            return redirect(url_for("dashboard.dashboard_home"))

        flash("Invalid username/email or password.", "danger")

    return render_template("login.html")


@auth.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully.", "success")

    return redirect(url_for("auth.login"))


@auth.route("/forgot-password")
def forgot_password():

    return "<h3>Forgot Password Module Coming Next</h3>"
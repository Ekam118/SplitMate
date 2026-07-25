from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from models import User
import random
import time

from flask_mail import Message
from extensions import db, mail

auth = Blueprint("auth", __name__)

# -----------------------------------------------------DEFAULT PAGE------------------------------------------------
@auth.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard_home"))
    return redirect(url_for("auth.login"))

# --------------------------------------------------------REGISTER------------------------------------------------
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

# ------------------------------------------------------LOGIN----------------------------------------------------
@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        login = request.form["login"].strip().lower()
        password = request.form["password"]
        user = User.query.filter(or_(User.username == login,User.email == login)).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id

            flash("Login successful.", "success")
            return redirect(url_for("dashboard.dashboard_home"))

        flash("Invalid username/email or password.", "danger")

    return render_template("login.html")

# ------------------------------------------------------LOGOUT--------------------------------------------------
@auth.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully.", "success")

    return redirect(url_for("auth.login"))


# --------------------------------------------------FORGOT PASSWORD----------------------------------------------
@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"].strip().lower()

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("No account found with this email.", "danger")
            return redirect(url_for("auth.forgot_password"))

        otp = str(random.randint(100000, 999999))

        session["reset_email"] = email
        session["reset_otp"] = otp
        session["otp_time"] = time.time()

        msg = Message(
            subject="SplitMate Password Reset OTP",
            recipients=[email]
        )

        msg.body = f"""
Hello {user.fullname},

Your SplitMate Password Reset OTP is

{otp}

This OTP is valid for 5 minutes.

If you didn't request this, simply ignore this email.

Team SplitMate
"""

        mail.send(msg)

        flash("OTP sent successfully to your email.", "success")
        return redirect(url_for("auth.verify_otp"))
    return render_template("forgot_password.html")



# -----------------------------------------------------VERIFY OTP--------------------------------------------------
@auth.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():

    if "reset_otp" not in session:
        flash("Please request a new OTP.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":

        entered_otp = request.form["otp"].strip()

        # OTP expires after 5 minutes (300 seconds)
        if time.time() - session["otp_time"] > 300:

            session.pop("reset_otp", None)
            session.pop("reset_email", None)
            session.pop("otp_time", None)

            flash("OTP has expired. Please request a new one.", "danger")
            return redirect(url_for("auth.forgot_password"))

        if entered_otp != session["reset_otp"]:

            flash("Invalid OTP.", "danger")
            return redirect(url_for("auth.verify_otp"))

        flash("OTP verified successfully.", "success")
        return redirect(url_for("auth.reset_password"))
    return render_template("verify_otp.html")



# --------------------------------------------------RESET PASSWORD-----------------------------------------------
@auth.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    if "reset_email" not in session:
        flash("Please verify OTP first.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.reset_password"))

        user = User.query.filter_by(email=session["reset_email"]).first()

        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("auth.forgot_password"))

        user.password = generate_password_hash(password)

        db.session.commit()

        session.pop("reset_email", None)
        session.pop("reset_otp", None)
        session.pop("otp_time", None)

        flash("Password reset successfully. Please login.", "success")

        return redirect(url_for("auth.login"))

    return render_template("reset_password.html")

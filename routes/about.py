from flask import Blueprint, render_template, session, redirect, url_for

about = Blueprint("about",__name__,url_prefix="/about")

# ----------------------------------------------ABOUT PAGE--------------------------------------------------------
@about.route("/")
def about_home():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    return render_template("about.html")
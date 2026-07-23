from flask import Blueprint,render_template, redirect, url_for, session
from models import Notification
from extensions import db


notifications = Blueprint( "notifications", __name__, url_prefix="/notifications")

@notifications.route("/")
def notification_home():

    if "user_id" not in session:

        return redirect( url_for("auth.login"))

    user_id = session["user_id"]


    notifications = Notification.query.filter_by(user_id=user_id).order_by( Notification.created_at.desc()).all()
    return render_template( "notifications.html", notifications=notifications)

# --------------------------------------------------
# Mark Notification as Read
# --------------------------------------------------
@notifications.route("/<int:notification_id>/read" , methods=["POST"])
def mark_read(notification_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))


    notification = Notification.query.filter_by(id=notification_id,user_id=session["user_id"]).first_or_404()

    notification.is_read = True
    db.session.commit()


    return redirect(url_for("notifications.notification_home"))
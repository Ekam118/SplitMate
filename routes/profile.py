from flask import  Blueprint, render_template, redirect, url_for, session, request, flash, current_app
from models import User
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os
from extensions import db

profile = Blueprint("profile",__name__,url_prefix="/profile")

@profile.route("/")
def profile_home():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get_or_404(session["user_id"])
    
    return render_template("profile/profile.html",user=user)


# ------------------------------------------------------------EDIT PROFILE-------------------------------------------------------------

@profile.route("/edit", methods=["GET", "POST"])
def edit_profile():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    user = User.query.get_or_404(session["user_id"])

    if request.method == "POST":

        user.fullname = request.form["fullname"]
        user.email = request.form["email"]

        # Profile image upload

        if "profile_image" in request.files:

            image = request.files["profile_image"]

            if image.filename:

                filename = secure_filename(image.filename)

                upload_path = current_app.config["UPLOAD_PROFILE"]

                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)

                image.save(
                    os.path.join(upload_path, filename)
                )

                user.profile_image = filename


        db.session.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )
        return redirect(
            url_for("profile.profile_home")
        )
    return render_template(
        "profile/edit_profile.html",user=user
    )

# ----------------------------------------------------------------change password-------------------------------------------------------------------

@profile.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )


    user = User.query.get_or_404(
        session["user_id"]
    )


    if request.method == "POST":

        current_password = request.form["current_password"]

        new_password = request.form["new_password"]

        confirm_password = request.form["confirm_password"]



        # Check old password

        if not check_password_hash(
            user.password,
            current_password
        ):

            flash(
                "Current password is incorrect.",
                "danger"
            )

            return redirect(
                url_for(
                    "profile.change_password"
                )
            )



        # Check new password match

        if new_password != confirm_password:

            flash(
                "New passwords do not match.",
                "danger"
            )

            return redirect(
                url_for(
                    "profile.change_password"
                )
            )



        user.password = generate_password_hash(
            new_password
        )


        db.session.commit()


        flash(
            "Password changed successfully.",
            "success"
        )


        return redirect(
            url_for(
                "profile.profile_home"
            )
        )



    return render_template(
        "profile/change_password.html"
    )



# ---------------------------------------------------------------DELETE ACCOUNT-------------------------------------------------------------------

@profile.route("/delete-account", methods=["GET", "POST"])
def delete_account():

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )


    user = User.query.get_or_404(
        session["user_id"]
    )


    if request.method == "POST":


        # Delete notifications

        for notification in user.notifications:
            db.session.delete(notification)



        # Delete settlements
        # (both sent and received)

        for settlement in (
            user.sent_settlements +
            user.received_settlements
        ):

            db.session.delete(settlement)



        # Delete expense participants

        for participant in user.expense_participants:

            db.session.delete(participant)



        # Delete groups created by user
        # Cascade will delete:
        # GroupMember
        # Expenses
        # Settlements

        for group in user.groups:

            db.session.delete(group)



        # Delete group memberships

        for membership in user.group_memberships:

            db.session.delete(membership)



        # Delete user

        db.session.delete(user)


        db.session.commit()



        session.clear()


        flash(
            "Account deleted successfully.",
            "success"
        )


        return redirect(
            url_for("auth.login")
        )



    return render_template(
        "profile/delete_account.html"
    )
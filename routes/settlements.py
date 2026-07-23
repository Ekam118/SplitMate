from flask import Blueprint, render_template, redirect, url_for, session, flash
from models import Settlement, Notification
from extensions import db


settlements = Blueprint( "settlements", __name__, url_prefix="/settlements")


# --------------------------------------------------
# Show User Settlements
# --------------------------------------------------

@settlements.route("/")
def settlement_home():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))


    user_id = session["user_id"]


    settlements = Settlement.query.filter(
        (Settlement.payer_id == user_id) |
        (Settlement.receiver_id == user_id)
    ).order_by(
        Settlement.created_at.desc()
    ).all()


    return render_template(
        "settlements/settlements.html",
        settlements=settlements
    )


# --------------------------------------------------
# Send Payment
# --------------------------------------------------

@settlements.route("/<int:settlement_id>/send", methods=["POST"])
def send_payment(settlement_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    settlement = Settlement.query.get_or_404(settlement_id)

    # Only payer can send payment
    if settlement.payer_id != user_id:

        flash(
            "Only payer can send the payment.",
            "danger"
        )

        return redirect(
            url_for("settlements.settlement_home")
        )

    # Payment already sent
    if settlement.status != "Pending":

        flash(
            "Payment has already been sent.",
            "warning"
        )

        return redirect(
            url_for("settlements.settlement_home")
        )

    settlement.status = "Payment Sent"

    notification = Notification(

        user_id=settlement.receiver_id,

        message=f"{settlement.payer.fullname} has sent the payment of ₹{settlement.amount}. Please confirm."

    )

    db.session.add(notification)

    db.session.commit()

    flash(
        "Payment sent successfully.",
        "success"
    )

    return redirect(
        url_for("settlements.settlement_home")
    )

# --------------------------------------------------
# Confirm Payment
# --------------------------------------------------

@settlements.route("/<int:settlement_id>/confirm", methods=["POST"])
def confirm_payment(settlement_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    settlement = Settlement.query.get_or_404(settlement_id)

    # Only receiver can confirm
    if settlement.receiver_id != user_id:

        flash(
            "Only receiver can confirm this payment.",
            "danger"
        )

        return redirect(
            url_for("settlements.settlement_home")
        )

    if settlement.status != "Payment Sent":

        flash(
            "Payment has not been sent yet.",
            "warning"
        )

        return redirect(
            url_for("settlements.settlement_home")
        )

    settlement.status = "Paid"

    notification = Notification(

        user_id=settlement.payer_id,

        message=f"{settlement.receiver.fullname} confirmed your payment of ₹{settlement.amount}."

    )

    db.session.add(notification)

    db.session.commit()

    flash(
        "Payment confirmed successfully.",
        "success"
    )

    return redirect(
        url_for("settlements.settlement_home")
    )


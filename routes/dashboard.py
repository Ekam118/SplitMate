from flask import Blueprint, render_template, session, redirect, url_for
from models import GroupMember, Expense, ExpenseParticipant, Settlement

dashboard = Blueprint("dashboard", __name__)

@dashboard.route("/dashboard")
def dashboard_home():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    # ---------------- TOTAL GROUPS ----------------
    total_groups = (GroupMember.query.filter_by(user_id=user_id).count())

    # ---------------- USER GROUP IDS ----------------
    memberships = GroupMember.query.filter_by(user_id=user_id).all()
    group_ids = [
        member.group_id
        for member in memberships
    ]

    # ---------------- TOTAL SPENDING ----------------
    total_spending = 0
    if group_ids:
        expenses = Expense.query.filter(Expense.group_id.in_(group_ids)).all()
        for expense in expenses:
            total_spending += expense.amount

    # ---------------- YOUR SHARE ----------------
    your_share = 0
    participant_expenses = ExpenseParticipant.query.filter_by(user_id=user_id).all()
    for participant in participant_expenses:
        your_share += participant.share_amount or 0


    # ---------------- PENDING SETTLEMENT ----------------
    # Amount user has to pay to others

    pending_settlement = 0
    settlements = Settlement.query.filter(
        Settlement.payer_id == user_id,
        Settlement.status.in_(["Pending", "Payment Sent"])).all()

    for settlement in settlements:
        pending_settlement += settlement.amount

    # ---------------- RECENT EXPENSES ----------------
    recent_expenses = []
    if group_ids:

        recent_expenses = (
            Expense.query
            .filter(
                Expense.group_id.in_(group_ids)
            )
            .order_by(
                Expense.created_at.desc()
            )
            .limit(5)
            .all()
        )

    return render_template("dashboard.html",
        total_groups=total_groups,
        total_spending=total_spending,
        your_share=your_share,
        pending_settlement=pending_settlement,
        recent_expenses=recent_expenses
    )
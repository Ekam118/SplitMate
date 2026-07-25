from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from models import GroupMember, Group, ExpenseParticipant, Expense, Settlement
from extensions import db
from datetime import date

balances = Blueprint("balances",__name__,url_prefix="/balances")


# ------------------------------------------------Balance Home - Show User Groups------------------------------------------------------

@balances.route("/")
def balance_home():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    memberships = GroupMember.query.filter_by(user_id=user_id).all()
    groups = [member.group for member in memberships]

    return render_template("balances/balances.html",groups=groups)



# --------------------------------------------------------Group Balance Calculation----------------------------------------------------

@balances.route("/<int:group_id>")
def group_balance(group_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    membership = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()

    if not membership:
        flash("You are not a member of this group.", "danger")
        return redirect(url_for("balances.balance_home"))

    group = Group.query.get_or_404(group_id)

    participants = (ExpenseParticipant.query.join(Expense).filter( Expense.group_id == group_id).all())

    balance_data = {}

    for participant in participants:
        uid = participant.user_id

        if uid not in balance_data:
            balance_data[uid] = {

                "user": participant.user,
                "paid": 0,
                "share": 0,
                "balance": 0
                }


        balance_data[uid]["paid"] += (participant.amount_paid or 0)
        balance_data[uid]["share"] += (participant.share_amount or 0)

    # Calculate balance

    for uid in balance_data:

        balance_data[uid]["balance"] = round(balance_data[uid]["paid"] - balance_data[uid]["share"],2)


# REMOVE COMPLETED SETTLEMENTS FROM BALANCE

    paid_settlements = Settlement.query.filter_by(group_id=group_id,status="Paid").all()
    
    for settlement in paid_settlements:


        # payer paid receiver
        if settlement.payer_id in balance_data:

            balance_data[settlement.payer_id]["balance"] += settlement.amount



        # receiver received money
        if settlement.receiver_id in balance_data:

            balance_data[settlement.receiver_id]["balance"] -= settlement.amount

    # WHO PAYS WHOM CALCULATION
    creditors = []
    debtors = []

    for data in balance_data.values():

        if data["balance"] > 0:

            creditors.append({
                "user": data["user"],
                "amount": data["balance"]

            })

        elif data["balance"] < 0:
            debtors.append({
                "user": data["user"],
                "amount": abs(data["balance"])
            })

    # CHECK EXISTING PENDING SETTLEMENT REQUESTS

    pending_settlements = Settlement.query.filter(
    Settlement.group_id == group_id,
    Settlement.status.in_(["Pending", "Payment Sent"])).all()        
    pending_pairs = []
            
    for settlement in pending_settlements:

        pending_pairs.append((settlement.payer_id,settlement.receiver_id,round(settlement.amount, 2)))

    settlements = []
    i = 0
    j = 0

    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]
        amount = min(debtor["amount"],creditor["amount"])
        settlements.append({"payer": debtor["user"],"receiver": creditor["user"],"amount": round(amount,2)})
        debtor["amount"] -= amount
        creditor["amount"] -= amount

        if debtor["amount"] == 0:
            i += 1

        if creditor["amount"] == 0:
            j += 1

    return render_template("balances/group_balance.html",

    group=group,
    balances=balance_data.values(),
    settlements=settlements,
    pending_pairs=pending_pairs,
    current_user_id=user_id
)


# -------------------------------------------------CREATE SETTLEMENT-----------------------------------------------
    

@balances.route("/<int:group_id>/settle", methods=["POST"])
def create_settlement(group_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))


    payer_id = int(request.form["payer_id"])
    receiver_id = int(request.form["receiver_id"])
    amount = float(request.form["amount"])


    existing_settlement = Settlement.query.filter(
    Settlement.group_id == group_id,
    Settlement.payer_id == payer_id,
    Settlement.receiver_id == receiver_id,
    Settlement.status.in_(["Pending", "Payment Sent"])).first()


    if existing_settlement:

        flash("A pending settlement already exists between these users.","warning")
        return redirect(url_for("balances.group_balance",group_id=group_id))

    settlement = Settlement(
        group_id=group_id,
        payer_id=payer_id,
        receiver_id=receiver_id,
        amount=amount,
        payment_method="Pending",
        settlement_date=date.today(),
        status="Pending"
    )


    db.session.add(settlement)
    db.session.commit()
    flash("Settlement request created successfully.","success")


    return redirect(url_for("balances.group_balance",group_id=group_id))
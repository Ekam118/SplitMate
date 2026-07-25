from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime

from extensions import db
from models import Expense, Group, ExpenseParticipant, GroupMember

expenses = Blueprint("expenses", __name__, url_prefix="/expenses")


# -------------------------------------------------My Expenses----------------------------------------------------
@expenses.route("/")
def expenses_home():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    group_ids = [member.group_id for member in GroupMember.query.filter_by(user_id=session["user_id"]).all()]
    if group_ids:
        expenses = (Expense.query.filter(Expense.group_id.in_(group_ids)).order_by(Expense.created_at.desc()).all())
    else:
        expenses = []
    return render_template("expenses/expenses.html",expenses=expenses)


# -------------------------------------------------Add Expense-------------------------------------------------------
@expenses.route("/add", methods=["GET", "POST"])
def add_expense():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    memberships = GroupMember.query.filter_by(user_id=session["user_id"]).all()
    groups = [member.group for member in memberships]

    if request.method == "POST":

        title = request.form["title"].strip()
        description = request.form["description"].strip()
        group_id = int(request.form["group_id"])

        # Check that the logged-in user belongs to the selected group
        membership = GroupMember.query.filter_by(group_id=group_id,user_id=session["user_id"]).first()

        if not membership:
            flash("You are not a member of this group.", "danger")
            return redirect(url_for("expenses.add_expense"))
        
        try:
            amount = float(request.form["amount"])
        except ValueError:
            flash("Invalid expense amount.", "danger")
            return redirect(url_for("expenses.add_expense"))

        if amount <= 0:
            flash("Expense amount must be greater than zero.", "danger")
            return redirect(url_for("expenses.add_expense"))
        category = request.form["category"]
        split_type = request.form["split_type"]
        currency = request.form["currency"]
        payment_method = request.form["payment_method"]
        expense_date = datetime.strptime(request.form["expense_date"],"%Y-%m-%d").date()

        if title == "":
            flash("Expense title is required.", "danger")
            return redirect(url_for("expenses.add_expense"))
        
        session["expense_data"] = {
        "group_id": group_id,
        "title": title,
        "description": description,
        "amount": amount,
        "category": category,
        "split_type": split_type,
        "currency": currency,
        "payment_method": payment_method,
        "expense_date": expense_date.strftime("%Y-%m-%d")
    }
        return redirect(url_for("expenses.expense_participants"))
    return render_template("expenses/add_expense.html",groups=groups)


# -----------------------------------------------Expense Participants-----------------------------------------------
@expenses.route("/participants", methods=["GET", "POST"])
def expense_participants():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    expense_data = session.get("expense_data")

    if not expense_data:
        flash("Please add expense details first.", "warning")
        return redirect(url_for("expenses.add_expense"))

    group = Group.query.get_or_404(expense_data["group_id"])
    membership = GroupMember.query.filter_by(group_id=group.id,user_id=session["user_id"]).first()
    if not membership:
        session.pop("expense_data", None)
        flash("You are not a member of this group.", "danger")
        return redirect(url_for("expenses.add_expense"))
    
    members = GroupMember.query.filter_by(group_id=group.id).all()

    if request.method == "POST":

        participant_ids = request.form.getlist("participants")

        if not participant_ids:
            flash("Please select at least one participant.", "warning")
            return redirect(url_for("expenses.expense_participants"))
        # Validate that all selected participants belong to this group
        valid_member_ids = {
            str(member.user_id)
            for member in members
        }
        for participant_id in participant_ids:
            if participant_id not in valid_member_ids:
                flash("Invalid participant selected.", "danger")
                return redirect(url_for("expenses.expense_participants"))

# -------------------------Validate Total Paid----------------------------

        total_paid = 0
        for user_id in participant_ids:
            try:
                paid_amount = float(request.form.get(f"paid_{user_id}",0))

                if paid_amount < 0:
                    flash("Paid amount cannot be negative.","danger")
                    return redirect(url_for("expenses.expense_participants")) 
                total_paid += paid_amount

            except ValueError:
                flash("Invalid paid amount.", "danger")
                return redirect(url_for("expenses.expense_participants"))

        if round(total_paid, 2) != round(expense_data["amount"], 2):
            flash(f"Total paid must equal {expense_data['currency']} {expense_data['amount']:.2f}","danger")
            return redirect(url_for("expenses.expense_participants"))
        

        # ---------------------------- Add Mode / Edit Mode -----------------------
        edit_mode = expense_data.get("edit_mode", False)
        if edit_mode:
            expense = Expense.query.get_or_404(expense_data["expense_id"])

            # remove old participant records
            ExpenseParticipant.query.filter_by(expense_id=expense.id).delete()
        else:
            expense = Expense(
                group_id=expense_data["group_id"],
                title=expense_data["title"],
                description=expense_data["description"],
                amount=expense_data["amount"],
                category=expense_data["category"],
                split_type=expense_data["split_type"],
                currency=expense_data["currency"],
                payment_method=expense_data["payment_method"],
                expense_date=datetime.strptime(expense_data["expense_date"],"%Y-%m-%d").date(),created_by=session["user_id"])
            
            db.session.add(expense)
            db.session.flush()
        # -----------------------------------Equal Split-------------------------------------

        if expense.split_type == "Equal":
            share = round(expense.amount / len(participant_ids), 2)
            total_assigned = 0
            for index, user_id in enumerate(participant_ids):
                final_share = share

        # --------------------Adjust rounding difference for last participant--------------
                if index == len(participant_ids) - 1:
                    final_share = round(expense.amount - total_assigned,2)
                total_assigned += final_share
                participant = ExpenseParticipant(
                    expense_id=expense.id,
                    user_id=int(user_id),
                    share_amount=final_share,
                    amount_paid=float(request.form.get(f"paid_{user_id}",0)))
                db.session.add(participant)



        # ---------------------------Exact Split-----------------------------------------

        elif expense.split_type == "Exact":
            total_share = 0
            for user_id in participant_ids:
                try:
                     share_amount = float(request.form.get(f"share_{user_id}",0))
                     if share_amount < 0:
                          flash("Share amount cannot be negative.","danger")
                          db.session.rollback()
                          return redirect(url_for("expenses.expense_participants"))
                     total_share += share_amount
                except ValueError:
                    flash("Invalid share amount.", "danger")
                    db.session.rollback()
                    return redirect(url_for("expenses.expense_participants"))
            if round(total_share, 2) != round(expense.amount, 2):
                flash("Total share amount must equal expense amount.","danger")
                db.session.rollback()
                return redirect(url_for("expenses.expense_participants"))
            for user_id in participant_ids:
                participant = ExpenseParticipant(
                    expense_id=expense.id,
                    user_id=int(user_id),
                    share_amount=float(request.form.get(f"share_{user_id}", 0)),
                    amount_paid=float(request.form.get(f"paid_{user_id}", 0)))
                db.session.add(participant)

        # ----------------------------Percentage Split-----------------------------------------

        elif expense.split_type == "Percentage":
            total_percentage = 0
            for user_id in participant_ids:
                try:
                    percentage = float(request.form.get(f"percentage_{user_id}", 0))
                    if percentage < 0:
                        flash("Percentage cannot be negative.", "danger")
                        db.session.rollback()
                        return redirect(url_for("expenses.expense_participants"))
                    if percentage > 100:
                        flash("Percentage cannot be greater than 100.", "danger")
                        db.session.rollback()
                        return redirect(url_for("expenses.expense_participants"))
                    total_percentage += percentage

                except ValueError:
                    flash("Invalid percentage.", "danger")
                    db.session.rollback()
                    return redirect(url_for("expenses.expense_participants"))
            if round(total_percentage, 2) != 100:
                flash("Total percentage must equal 100.","danger")
                db.session.rollback()
                return redirect(url_for("expenses.expense_participants"))
            for user_id in participant_ids:
                percentage = float(request.form.get(f"percentage_{user_id}", 0))
                if percentage < 0:
                    flash("Percentage cannot be negative.", "danger")
                    db.session.rollback()
                    return redirect(url_for("expenses.expense_participants"))

                share = expense.amount * percentage / 100
                participant = ExpenseParticipant(
                    expense_id=expense.id,
                    user_id=int(user_id),
                    percentage=percentage,
                    share_amount=share,
                    amount_paid=float(request.form.get(f"paid_{user_id}", 0)))

                db.session.add(participant)
        db.session.commit()
        session.pop("expense_data", None)

        if edit_mode:
            flash("Expense participants updated successfully.", "success")

        else:
            flash("Expense added successfully.", "success")
            
        return redirect(url_for("expenses.expense_dashboard",expense_id=expense.id))
    return render_template("expenses/participants.html",
                           group=group,
                           members=members,
                           expense_data=expense_data, 
                           old_participants=expense_data.get("old_participants", []))


# --------------------------------------------Expense Details-----------------------------------------------

@expenses.route("/<int:expense_id>")
def expense_dashboard(expense_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    expense = Expense.query.get_or_404(expense_id)
    membership = GroupMember.query.filter_by(group_id=expense.group_id,user_id=session["user_id"]).first()
    if not membership:
        flash("You are not a member of this group.", "danger")
        return redirect(url_for("expenses.expenses_home"))

    participants = ExpenseParticipant.query.filter_by(expense_id=expense.id).all()
    participant_count = len(participants)
    total_paid = sum(participant.amount_paid for participant in participants)
    total_due = expense.amount - total_paid
    return render_template("expenses/expense_dashboard.html",
        expense=expense,
        participants=participants,
        participant_count=participant_count,
        total_paid=total_paid,
        total_due=total_due
    )


# --------------------------------------------Edit Expense--------------------------------------------------------

@expenses.route("/<int:expense_id>/edit", methods=["GET", "POST"])
def edit_expense(expense_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    expense = Expense.query.get_or_404(expense_id)

    membership = GroupMember.query.filter_by(group_id=expense.group_id,user_id=session["user_id"]).first()

    if not membership:
        flash("You are not a member of this group.", "danger")
        return redirect(url_for("expenses.expenses_home"))

    if expense.created_by != session["user_id"]:

        flash("Only the expense creator can edit this expense.", "danger")
        return redirect(url_for("expenses.expense_dashboard",expense_id=expense.id))
    
    memberships = GroupMember.query.filter_by(user_id=session["user_id"]).all()
    groups = [member.group for member in memberships]

    if request.method == "POST":

        expense.title = request.form["title"].strip()
        expense.description = request.form["description"].strip()
        old_amount = expense.amount
        old_split_type = expense.split_type

        try:
            new_amount = float(request.form["amount"])
        except ValueError:
            flash("Invalid expense amount.", "danger")
            return redirect(url_for("expenses.edit_expense", expense_id=expense.id))


        new_split_type = request.form["split_type"]
        expense.amount = new_amount
        expense.split_type = new_split_type

        if expense.amount <= 0:
            flash("Expense amount must be greater than zero.", "danger")
            return redirect(url_for("expenses.edit_expense",expense_id=expense.id))
        
        expense.category = request.form["category"]
        expense.currency = request.form["currency"]
        expense.payment_method = request.form["payment_method"]
        expense.expense_date = datetime.strptime(request.form["expense_date"],"%Y-%m-%d").date()
        
        # If amount or split type changed
        if old_amount != new_amount or old_split_type != new_split_type:
            session["expense_data"] = {
                "edit_mode": True,
                "expense_id": expense.id,
                "group_id": expense.group_id,
                "title": expense.title,
                "description": expense.description,
                "amount": expense.amount,
                "category": expense.category,
                "split_type": expense.split_type,
                "currency": expense.currency,
                "payment_method": expense.payment_method,
                "expense_date": expense.expense_date.strftime("%Y-%m-%d"),
                "old_participants": [
                    {
                        "user_id": p.user_id,
                        "amount_paid": p.amount_paid, 
                        "share_amount": p.share_amount,
                        "percentage": p.percentage
                        }
                        for p in ExpenseParticipant.query.filter_by(expense_id=expense.id).all()]
                        }
            
            db.session.commit()
            return redirect(url_for("expenses.expense_participants"))
        
        else:

            db.session.commit()

            flash("Expense updated successfully.","success")
            return redirect(url_for("expenses.expense_dashboard",expense_id=expense.id))
        
    return render_template("expenses/edit_expense.html",expense=expense,groups=groups)


# ---------------------------------------------------Delete Expense------------------------------------------------

@expenses.route("/<int:expense_id>/delete", methods=["GET", "POST"])
def delete_expense(expense_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    expense = Expense.query.get_or_404(expense_id)
    membership = GroupMember.query.filter_by(
    group_id=expense.group_id,
    user_id=session["user_id"]).first()

    if not membership:
        flash("You are not a member of this group.","danger")
        return redirect(url_for("expenses.expenses_home"))

    if expense.created_by != session["user_id"]:

        flash("Only the expense creator can delete this expense.", "danger")
        return redirect(url_for("expenses.expense_dashboard",expense_id=expense.id))

    if request.method == "POST":

        db.session.delete(expense)

        db.session.commit()

        flash("Expense deleted successfully.", "success")

        return redirect(url_for("expenses.expenses_home"))

    return render_template("expenses/delete_expense.html",expense=expense)
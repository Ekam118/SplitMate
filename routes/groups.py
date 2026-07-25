from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime

from extensions import db
from models import Group, GroupMember, User, Expense, ExpenseParticipant ,Settlement

groups = Blueprint("groups", __name__, url_prefix="/groups")


# -------------------------------------------------My Groups -------------------------------------------------------

@groups.route("/")
def groups_home():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    memberships = (GroupMember.query.filter_by(user_id=session["user_id"]).order_by(GroupMember.joined_at.desc()).all())
    groups = [member.group for member in memberships]

    return render_template("groups/groups.html",groups=groups)


# ---------------------- Create Group ----------------------

@groups.route("/create", methods=["GET", "POST"])
def create_group():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        name = request.form["name"].strip()
        description = request.form["description"].strip()
        group_type = request.form["group_type"]

        trip_mode = True if request.form.get("trip_mode") else False

        trip_start_date = None
        trip_end_date = None

        if name == "":
            flash("Group name is required.", "danger")
            return redirect(url_for("groups.create_group"))

        existing = Group.query.filter_by(name=name,created_by=session["user_id"]).first()

        if existing:
            flash("You already created a group with this name.", "warning")
            return redirect(url_for("groups.create_group"))

        if trip_mode:

            start = request.form.get("trip_start_date")
            end = request.form.get("trip_end_date")

            if start == "" or end == "":
                flash("Trip dates are required.", "danger")
                return redirect(url_for("groups.create_group"))

            trip_start_date = datetime.strptime(start, "%Y-%m-%d").date()
            trip_end_date = datetime.strptime(end, "%Y-%m-%d").date()

            if trip_end_date < trip_start_date:

                flash("Trip end date cannot be before start date.","danger")
                return redirect(url_for("groups.create_group"))

        new_group = Group(
            name=name,
            description=description,
            group_type=group_type,
            trip_mode=trip_mode,
            trip_start_date=trip_start_date,
            trip_end_date=trip_end_date,
            created_by=session["user_id"]
        )

        db.session.add(new_group)
        db.session.flush()

        creator = GroupMember(
            group_id=new_group.id,
            user_id=session["user_id"],
            is_admin=True
        )

        db.session.add(creator)
        db.session.commit()

        flash("Group created successfully.", "success")

        return redirect(url_for("groups.groups_home"))

    return render_template("groups/create_group.html")

# ---------------------------------------------------------GroupDetails--------------------------------------------------

@groups.route("/<int:group_id>")
def group_dashboard(group_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    membership = GroupMember.query.filter_by(group_id=group_id,user_id=session["user_id"]).first_or_404()
    group = membership.group

    # Summary
    member_count = len(group.members)
    expense_count = len(group.expenses)
    total_amount = sum(exp.amount for exp in group.expenses)

    # Use 0 until Settlement module is ready
    settlement_count = Settlement.query.filter_by(group_id=group.id).count()

    # Recent Members
    recent_members = (GroupMember.query.filter_by(group_id=group.id).order_by(GroupMember.joined_at.desc()).limit(5).all())

    # Recent Expenses
    recent_expenses = (Expense.query.filter_by(group_id=group.id).order_by(Expense.created_at.desc()).limit(5).all())

    return render_template(
        "groups/group_dashboard.html",
        group=group,
        member_count=member_count,
        expense_count=expense_count,
        total_amount=total_amount,
        settlement_count=settlement_count,
        recent_members=recent_members,
        recent_expenses=recent_expenses
    )

# -------------------------------------------------------EDIT GROUP---------------------------------------------------
@groups.route("/<int:group_id>/edit", methods=["GET", "POST"])
def edit_group(group_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    membership = GroupMember.query.filter_by(
        group_id=group_id,
        user_id=session["user_id"]
    ).first_or_404()

    if not membership.is_admin:
        flash("Only the group admin can edit this group.", "warning")
        return redirect(url_for("groups.group_dashboard", group_id=group_id))

    group = membership.group

    if request.method == "POST":

        name = request.form["name"].strip()
        description = request.form["description"].strip()
        group_type = request.form["group_type"]

        existing = Group.query.filter(
            Group.name == name,
            Group.created_by == group.created_by,
            Group.id != group.id
        ).first()

        if existing:
            flash("Group name already exists.", "warning")
            return redirect(url_for("groups.edit_group", group_id=group.id))

        group.name = name
        group.description = description
        group.group_type = group_type

        if "trip_mode" in request.form:

            start_date = request.form.get("trip_start_date")
            end_date = request.form.get("trip_end_date")

            if not start_date or not end_date:
                flash("Trip dates are required when Trip Mode is enabled.", "danger")
                return redirect(url_for("groups.edit_group", group_id=group.id))

            group.trip_mode = True
            group.trip_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            group.trip_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

            if group.trip_end_date < group.trip_start_date:
                flash("Trip end date cannot be before start date.", "danger")
                return redirect(url_for("groups.edit_group", group_id=group.id))

        else:
            group.trip_mode = False
            group.trip_start_date = None
            group.trip_end_date = None

        db.session.commit()

        flash("Group updated successfully.", "success")

        return redirect(url_for("groups.group_dashboard", group_id=group.id))

    return render_template("groups/edit_group.html", group=group)


@groups.route("/<int:group_id>/delete", methods=["GET", "POST"])
def delete_group(group_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    membership = GroupMember.query.filter_by(
        group_id=group_id,
        user_id=session["user_id"]
    ).first_or_404()

    if not membership.is_admin:
        flash("Only the group admin can delete this group.", "warning")
        return redirect(url_for("groups.group_dashboard", group_id=group_id))

    group = membership.group

    pending_settlements = Settlement.query.filter_by(
    group_id=group.id,
    status="Pending").first()

    if pending_settlements:
        flash("This group has pending settlements. Complete them before deleting the group.","danger")
        return redirect(url_for("groups.group_dashboard", group_id=group.id))

    if request.method == "POST":

        db.session.delete(group)
        db.session.commit()

        flash("Group deleted successfully.", "success")

        return redirect(url_for("groups.groups_home"))

    return render_template("groups/delete_group.html", group=group)


# ----------------------------------------------------GROUP MEMBERS----------------------------------------------------

@groups.route("/<int:group_id>/members")
def group_members(group_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    membership = GroupMember.query.filter_by(group_id=group_id,user_id=session["user_id"]).first_or_404()
    group = membership.group

    members = GroupMember.query.filter_by(
        group_id=group.id
    ).all()

    return render_template(
        "groups/group_members.html",
        group=group,
        members=members
    )

# ------------------------------------------------------ADD MEMBER-----------------------------------------------------

@groups.route("/<int:group_id>/members/add", methods=["GET", "POST"])
def add_member(group_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    group = Group.query.get_or_404(group_id)
    admin = GroupMember.query.filter_by(group_id=group.id,user_id=session["user_id"],is_admin=True).first()
    if not admin:
        flash("Only the group admin can add members.", "danger")
        return redirect(url_for("groups.group_dashboard", group_id=group.id))

    if request.method == "POST":

        username = request.form["username"].strip()

        user = User.query.filter_by(username=username).first()

        if not user:
            flash("User not found.", "danger")

            return redirect(url_for("groups.add_member", group_id=group.id))
        
        # Prevent admin from adding himself again
        if user.id == session["user_id"]:
            flash("You are already the group admin.", "warning")
            return redirect(url_for("groups.add_member", group_id=group.id))

        existing = GroupMember.query.filter_by(group_id=group.id,user_id=user.id).first()

        if existing:
            flash("User is already a member.", "warning")
            return redirect(url_for("groups.add_member", group_id=group.id))

        member = GroupMember(group_id=group.id,user_id=user.id)

        db.session.add(member)
        db.session.commit()

        flash("Member added successfully.", "success")

        return redirect(
            url_for("groups.group_members", group_id=group.id)
        )

    return render_template(
        "groups/add_member.html",
        group=group
    )

# ----------------------------------------------------REMOVE MEMBER----------------------------------------------------

@groups.route("/<int:group_id>/members/<int:member_id>/remove",methods=["GET", "POST"])
def remove_member(group_id, member_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    group = Group.query.get_or_404(group_id)
    admin = GroupMember.query.filter_by(group_id=group.id,user_id=session["user_id"],is_admin=True).first()
    if not admin:
        flash("Only the group admin can remove members.", "danger")
        return redirect(url_for("groups.group_dashboard", group_id=group.id))

    member = GroupMember.query.filter_by(id=member_id,group_id=group.id).first_or_404()
    if request.method == "POST":
        if member.is_admin:
            flash("Group admin cannot be removed.", "danger")
            return redirect(url_for("groups.group_members",group_id=group.id))
        
        # Check if member is involved in any expense
        expense_history = (ExpenseParticipant.query.join(Expense).filter(Expense.group_id == group.id,ExpenseParticipant.user_id == member.user_id).first())
        if expense_history:
            flash("Cannot remove this member because they are involved in group expenses.","danger")
            return redirect(url_for("groups.group_members",group_id=group.id))
        db.session.delete(member)
        db.session.commit()
        flash("Member removed successfully.","success")
        return redirect(url_for("groups.group_members",group_id=group.id))
    return render_template("groups/delete_member.html",group=group,member=member)
from flask import Blueprint, render_template, request, session, redirect, url_for

from models import Group, Expense, GroupMember


search = Blueprint("search",__name__,url_prefix="/search")


@search.route("/")
def search_home():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    query = request.args.get("q")
    groups = []
    expenses = []

    user_id = session["user_id"]
    if query:
        # Groups user belongs to
        group_ids = [
            member.group_id
            for member in GroupMember.query.filter_by(
                user_id=user_id
            ).all()
        ]

        groups = Group.query.filter(
            Group.id.in_(group_ids),
            Group.name.ilike(f"%{query}%")
        ).all()

        # Expenses search
        expenses = Expense.query.filter(
            Expense.group_id.in_(group_ids),
            Expense.title.ilike(f"%{query}%")
        ).all()

    return render_template("search.html",
        groups=groups,
        expenses=expenses,
        query=query
    )
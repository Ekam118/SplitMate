from datetime import datetime
from extensions import db


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer,primary_key=True)
    fullname = db.Column(db.String(100),nullable=False)
    username = db.Column(db.String(50),unique=True,nullable=False)
    email = db.Column(db.String(120),unique=True,nullable=False)
    password = db.Column(db.String(255),nullable=False)
    profile_image = db.Column(db.String(255),nullable=False,default="default.png")
    created_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    groups = db.relationship("Group",backref="creator",lazy=True)
    expenses = db.relationship("Expense",backref="creator",lazy=True)
    group_memberships = db.relationship("GroupMember",backref="user",lazy=True)
    notifications = db.relationship("Notification",backref="user",lazy=True)
    sent_settlements = db.relationship("Settlement",foreign_keys="Settlement.payer_id",backref="payer",lazy=True)
    received_settlements = db.relationship("Settlement",foreign_keys="Settlement.receiver_id",backref="receiver",lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

# ----------------------------------------------------GROUP----------------------------------------------------------

class Group(db.Model):
    __tablename__ = "group" 

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    group_type = db.Column(db.String(50), nullable=False)
    trip_mode = db.Column(db.Boolean, default=False)
    trip_start_date = db.Column(db.Date)
    trip_end_date = db.Column(db.Date)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    members = db.relationship("GroupMember", backref="group", cascade="all, delete-orphan", lazy=True)
    expenses = db.relationship("Expense", backref="group", cascade="all, delete-orphan", lazy=True)
    settlements = db.relationship("Settlement", backref="group", cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f"<Group {self.name}>"


 #------------------------------------------------------GroupMember-----------------------------------------------------

class GroupMember(db.Model):
    __tablename__ = "group_member"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<GroupMember {self.user_id}>"


#-------------------------------------------------------EXPENSE--------------------------------------------------------

class Expense(db.Model):
    __tablename__ = "expense"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    split_type = db.Column(db.String(20), nullable=False)
    currency = db.Column(db.String(10), default="INR")
    payment_method = db.Column(db.String(20), nullable=False)
    expense_date = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # paid_by = db.Column(db.Integer,db.ForeignKey("users.id"))
    participants = db.relationship("ExpenseParticipant",backref="expense",cascade="all, delete-orphan",lazy=True)

    def __repr__(self):
        return f"<Expense {self.title}>"


#-------------------------------------------------ExpenseParticipant---------------------------------------------------

class ExpenseParticipant(db.Model):
    __tablename__ = "expense_participant"

    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer,db.ForeignKey("expense.id"),nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    amount_paid = db.Column(db.Float,default=0)
    share_amount = db.Column(db.Float,default=0)
    percentage = db.Column(db.Float,default=0)
    ratio = db.Column(db.Float,default=0)
    user = db.relationship("User",backref="expense_participants")

    def __repr__(self):
        return f"<ExpenseParticipant {self.id}>"


#----------------------------------------------------SETTLEMENT-------------------------------------------------------

class Settlement(db.Model):
    __tablename__ = "settlement"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)

    payer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)

    settlement_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Settlement {self.id}>"

#------------------------------------------------NOTIFICATION----------------------------------------------------

class Notification(db.Model):
    __tablename__ = "notification"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.id}>"
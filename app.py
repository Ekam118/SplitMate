from flask import Flask
from config import Config
from extensions import db, migrate, mail

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    import models

    from routes.auth import auth
    from routes.dashboard import dashboard
    from routes.groups import groups
    from routes.expenses import expenses
    from routes.settlements import settlements
    from routes.balances import balances
    from routes.notifications import notifications
    from routes.profile import profile
    from routes.search import search
    from routes.about import about


    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(groups)
    app.register_blueprint(expenses)
    app.register_blueprint(balances)
    app.register_blueprint(settlements)
    app.register_blueprint(notifications)
    app.register_blueprint(profile)
    app.register_blueprint(search)
    app.register_blueprint(about)


    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
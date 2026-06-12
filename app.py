from flask import Flask, redirect, request, url_for
from flask_login import LoginManager

import database
import models
from blueprints import allocations, api, auth, dashboard, prefixes
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    Config.INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

    database.init_app(app)
    with app.app_context():
        database.init_db()

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        row = models.get_user_by_id(user_id)
        if row is None:
            return None
        return models.User(row["id"], row["username"])

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(prefixes.bp)
    app.register_blueprint(allocations.bp)
    app.register_blueprint(api.bp)

    @app.before_request
    def require_setup():
        # Allow static assets through untouched.
        if request.endpoint == "static":
            return None

        if models.user_count() == 0:
            if request.endpoint != "auth.setup":
                return redirect(url_for("auth.setup"))
        elif request.endpoint == "auth.setup":
            return redirect(url_for("auth.login"))

        return None

    @app.context_processor
    def inject_globals():
        return {"allocation_types": ["Infrastructure", "Customer", "VPS", "Lab", "Reserved"]}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

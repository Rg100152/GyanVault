"""
GyanVault — Curated Educational Resource Hub
============================================

Main Flask application.  Run it with::

    python seed_library.py     # one time, fills the vault
    python app.py              # http://127.0.0.1:5000
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, render_template, request

from database import close_db, init_db
from routes.api_routes import api_bp
from routes.library_routes import library_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("GYANVAULT_SECRET", "gyanvault-dev-key-raj-gautam"),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )
    if hasattr(app, "json"):
        app.json.sort_keys = False  # keep API payload order predictable

    # Make sure the database file and tables exist before the first request.
    init_db()

    app.register_blueprint(library_bp)
    app.register_blueprint(api_bp)
    app.teardown_appcontext(close_db)

    @app.context_processor
    def inject_globals():
        return {"brand": "GyanVault", "author": "Raj Gautam"}

    @app.errorhandler(404)
    def handle_404(error):  # noqa: ARG001
        if request.path.startswith("/api/"):
            return jsonify({"error": "Endpoint not found", "status": 404}), 404
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def handle_500(error):  # noqa: ARG001
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error", "status": 500}), 500
        return render_template("404.html", server_error=True), 500

    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        print("GyanVault database initialised.")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

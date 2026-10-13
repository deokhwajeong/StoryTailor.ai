"""StoryTailor: a personalized reading platform for elementary classrooms."""

import os

import click
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from . import db
from .config import Config


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if app.config["DATABASE"] != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(app.config["DATABASE"])), exist_ok=True)

    db.init_app(app)

    from .routes import books, classroom, meta, privacy, stories
    for module in (meta, classroom, stories, books, privacy):
        app.register_blueprint(module.bp)

    @app.errorhandler(HTTPException)
    def json_error(e):
        return jsonify({"error": e.description}), e.code

    @app.after_request
    def headers(resp):
        origin = request.headers.get("Origin")
        if origin and origin in app.config["ALLOWED_ORIGINS"]:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Student-Code"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
            resp.headers["Vary"] = "Origin"
        # Student content should never sit in shared or proxy caches.
        resp.headers["Cache-Control"] = "no-store"
        return resp

    _register_cli(app)
    return app


def _register_cli(app: Flask) -> None:
    from .privacy import hash_secret, new_teacher_token, purge_expired

    @app.cli.command("init-db")
    def init_db_command():
        db.init_db()
        click.echo("Initialized the database.")

    @app.cli.command("create-teacher")
    @click.argument("display_name")
    def create_teacher(display_name):
        """Create a teacher account and print its API token (shown once)."""
        token = new_teacher_token()
        conn = db.get_db()
        conn.execute(
            "INSERT INTO teachers (display_name, token_hash, created_at) VALUES (?, ?, ?)",
            (display_name, hash_secret(token), db.utcnow()),
        )
        conn.commit()
        click.echo(f"Teacher token for {display_name} (store it now, it is not shown again):\n{token}")

    @app.cli.command("seed-demo")
    @click.option("--from-file", "from_file", type=click.Path(exists=True, dir_okay=False),
                  help="Synthetic dataset JSON (must have metadata.is_synthetic = true).")
    @click.option("--seed", default=2026, show_default=True)
    def seed_demo(from_file, seed):
        """Load fictional demo classrooms. Never use with real student data."""
        from pathlib import Path

        from . import demo

        out = Path(app.instance_path) / "demo_access_codes.csv"
        try:
            result = demo.load_file(Path(from_file), out) if from_file else demo.generate(out, seed=seed)
        except demo.NotSynthetic as e:
            raise click.ClickException(str(e))
        token = result.pop("teacher_token")
        click.echo(f"Seeded demo data: {result}")
        click.echo(f"Demo teacher token: {token}")
        click.echo(f"Student access codes written to {out}")

    @app.cli.command("purge-expired")
    def purge_command():
        """Apply the retention policy. Run daily from cron."""
        click.echo(purge_expired(app.config["RETENTION_DAYS"]))

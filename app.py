from __future__ import annotations

import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, abort, current_app, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "site_data.json"
DATABASE = BASE_DIR / "instance" / "lgu_socorro.sqlite"


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DATABASE"] = DATABASE
    DATABASE.parent.mkdir(exist_ok=True)
    secret_file = DATABASE.parent / "session-secret.txt"
    if not secret_file.exists():
        secret_file.write_text(secrets.token_hex(32), encoding="utf-8")
    app.config["SECRET_KEY"] = os.environ.get("SOCORRO_SECRET_KEY") or secret_file.read_text(encoding="utf-8")
    staff_file = DATABASE.parent / "staff-access.json"
    if not staff_file.exists():
        staff_file.write_text(json.dumps({"username": "staff", "password": secrets.token_urlsafe(18)}, indent=2), encoding="utf-8")
    staff = json.loads(staff_file.read_text(encoding="utf-8"))
    app.config["STAFF_PASSWORD_HASH"] = generate_password_hash(os.environ.get("SOCORRO_STAFF_PASSWORD") or staff["password"])
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    if test_config:
        app.config.update(test_config)

    @app.before_request
    def before_request() -> None:
        g.site = load_site_data()
        session.setdefault("csrf", secrets.token_urlsafe(32))

    @app.teardown_appcontext
    def close_db(_error: Exception | None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.route("/")
    def home():
        data = g.site
        return render_template(
            "home.html",
            title="LGU Socorro",
            posts=data["posts"][:3],
            events=data["events"][:3],
        )

    @app.route("/about/")
    def about():
        return render_template("about.html", title="About Socorro")

    @app.route("/news/")
    def news():
        query = request.args.get("q", "").strip().lower()
        selected_type = request.args.get("type", "all")
        if selected_type not in ("all", "news", "events"):
            selected_type = "all"
        posts = [{**item, "kind": "news"} for item in g.site["posts"]]
        posts += [{**item, "kind": "events"} for item in g.site["events"]]
        if selected_type != "all":
            posts = [post for post in posts if post["kind"] == selected_type]
        if query:
            posts = [
                post
                for post in posts
                if query in f"{post['title']} {post['excerpt']} {post.get('body', '')}".lower()
            ]
        posts.sort(key=lambda post: post["date"], reverse=True)
        return render_template("listing.html", title="News & Events", items=posts, query=query, selected_type=selected_type)

    @app.route("/news/<slug>/")
    def news_detail(slug: str):
        post = find_by_slug(g.site["posts"], slug)
        if not post:
            abort(404)
        return render_template("detail.html", title=post["title"], item=post, kind="news")

    @app.route("/events/")
    def events():
        return redirect(url_for("news", type="events", q=request.args.get("q", "")), code=301)

    @app.route("/events/<slug>/")
    def event_detail(slug: str):
        event = find_by_slug(g.site["events"], slug)
        if not event:
            legacy_event = next((item for item in g.site["events"] if item.get("legacy_slug") == slug), None)
            if legacy_event:
                return redirect(url_for("event_detail", slug=legacy_event["slug"]), code=301)
            abort(404)
        return render_template("detail.html", title=event["title"], item=event, kind="events")

    @app.route("/transparency/")
    def transparency():
        category = request.args.get("category", "All")
        documents = g.site["transparency"]
        categories = ["All"] + sorted({doc["category"] for doc in documents})
        if category != "All":
            documents = [doc for doc in documents if doc["category"] == category]
        return render_template(
            "transparency.html",
            title="Transparency",
            documents=documents,
            categories=categories,
            selected=category,
        )

    @app.route("/tourism/")
    def tourism():
        return render_template("tourism.html", title="Tourism")

    @app.route("/services/", methods=["GET", "POST"])
    def services():
        if request.method == "POST":
            form = request.form
            required = ["name", "email", "service", "details"]
            if any(not form.get(field, "").strip() for field in required):
                flash("Please complete all required service request fields.", "error")
            else:
                db = get_db()
                db.execute(
                    """
                    INSERT INTO service_requests
                    (name, email, phone, service, details, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        form["name"].strip(),
                        form["email"].strip(),
                        form.get("phone", "").strip(),
                        form["service"].strip(),
                        form["details"].strip(),
                        datetime.utcnow().isoformat(timespec="seconds"),
                    ),
                )
                db.commit()
                flash("Your service request was received. LGU staff can review it in the submissions page.", "success")
                return redirect(url_for("services"))
        return render_template("services.html", title="Services")

    @app.route("/contact/", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            form = request.form
            required = ["name", "email", "message"]
            if any(not form.get(field, "").strip() for field in required):
                flash("Please complete your name, email, and message.", "error")
            else:
                db = get_db()
                db.execute(
                    """
                    INSERT INTO contact_messages
                    (name, email, subject, message, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        form["name"].strip(),
                        form["email"].strip(),
                        form.get("subject", "").strip(),
                        form["message"].strip(),
                        datetime.utcnow().isoformat(timespec="seconds"),
                    ),
                )
                db.commit()
                flash("Thank you. Your message has been saved.", "success")
                return redirect(url_for("contact"))
        return render_template("contact.html", title="Contact")

    @app.route("/office/agriculture/")
    def agriculture_office():
        return render_template("office.html", title="Agriculture Office", office=g.site["agriculture_office"])

    @app.route("/departments/")
    def departments():
        branch = request.args.get("branch", "all")
        if branch not in ("all", "executive", "legislative"):
            branch = "all"
        return render_template("departments.html", title="Departments", department_branch=branch, department_query=request.args.get("q", "").strip())

    @app.route("/departments/<slug>/", methods=["GET", "POST"])
    def department_detail(slug):
        office = find_by_slug(g.site["departments"], slug)
        if office is None:
            abort(404)
        error = None
        if request.method == "POST":
            verify_csrf()
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            message = request.form.get("message", "").strip()
            kind = request.form.get("kind", "")
            if not name or len(name) > 120 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 254 or not message or len(message) > 3000 or kind not in INQUIRY_KINDS:
                error = "Enter your name, a valid email, an inquiry type, and a message of up to 3,000 characters."
            else:
                reference = secrets.token_hex(12).upper()
                now = datetime.now(timezone.utc).isoformat(timespec="seconds")
                db = get_db()
                db.execute("INSERT INTO department_requests (reference, department, name, email, kind, message, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 'New', ?, ?)", (reference, slug, name, email, kind, message, now, now))
                db.commit()
                flash("Your inquiry was saved for staff review. Keep your reference to check its status.", "success")
                return redirect(url_for("department_track", reference=reference), code=303)
        return render_template("department_detail.html", title=office["name"], office=office, inquiry_kinds=INQUIRY_KINDS, error=error), (400 if error else 200)

    @app.route("/departments/track/")
    def department_track():
        reference = request.args.get("reference", "").strip().upper()
        record = get_db().execute("SELECT reference, department, status, created_at, updated_at FROM department_requests WHERE reference = ?", (reference,)).fetchone() if reference else None
        office = find_by_slug(g.site["departments"], record["department"]) if record else None
        return render_template("department_track.html", title="Track an inquiry", record=record, office=office, reference=reference)

    @app.route("/staff/login/", methods=["GET", "POST"])
    def staff_login():
        if request.method == "POST":
            verify_csrf()
            if request.form.get("username") == "staff" and check_password_hash(app.config["STAFF_PASSWORD_HASH"], request.form.get("password", "")):
                session.clear()
                session["staff"] = True
                session["csrf"] = secrets.token_urlsafe(32)
                return redirect(url_for("submissions"), code=303)
            flash("The username or password is incorrect.", "error")
        return render_template("staff_login.html", title="Staff sign in")

    @app.route("/staff/logout/", methods=["POST"])
    def staff_logout():
        verify_csrf()
        session.clear()
        return redirect(url_for("home"), code=303)

    @app.route("/staff/department-requests/<int:request_id>/", methods=["POST"])
    def update_department_request(request_id):
        if not session.get("staff"):
            abort(403)
        verify_csrf()
        status = request.form.get("status")
        if status not in ("New", "In review", "Resolved"):
            abort(400)
        db = get_db()
        result = db.execute("UPDATE department_requests SET status = ?, updated_at = ? WHERE id = ?", (status, datetime.now(timezone.utc).isoformat(timespec="seconds"), request_id))
        if not result.rowcount:
            abort(404)
        db.commit()
        flash("Inquiry status updated.", "success")
        return redirect(url_for("submissions"), code=303)

    @app.route("/submissions/")
    def submissions():
        if not session.get("staff"):
            return redirect(url_for("staff_login"))
        db = get_db()
        contacts = db.execute("SELECT * FROM contact_messages ORDER BY id DESC").fetchall()
        services_rows = db.execute("SELECT * FROM service_requests ORDER BY id DESC").fetchall()
        return render_template(
            "submissions.html",
            title="Submissions",
            contacts=contacts,
            service_requests=services_rows,
            department_requests=db.execute("SELECT * FROM department_requests ORDER BY id DESC").fetchall(),
            department_names={office["slug"]: office["name"] for office in g.site["departments"]},
        )

    @app.route("/search/")
    def search():
        query = request.args.get("q", "").strip().lower()
        results: list[dict[str, str]] = []
        if query:
            for collection, route_name in (("posts", "news_detail"), ("events", "event_detail")):
                for item in g.site[collection]:
                    haystack = f"{item['title']} {item['excerpt']} {item.get('body', '')}".lower()
                    if query in haystack:
                        results.append(
                            {
                                "title": item["title"],
                                "excerpt": item["excerpt"],
                                "url": url_for(route_name, slug=item["slug"]),
                            }
                        )
            for doc in g.site["transparency"]:
                haystack = f"{doc['title']} {doc['category']} {doc['year']}".lower()
                if query in haystack:
                    results.append({"title": doc["title"], "excerpt": doc["category"], "url": doc["url"]})
            for collection, endpoint in (("services", "services"), ("tourism", "tourism"), ("departments", "department_detail")):
                for item in g.site[collection]:
                    if query in f"{item['name']} {item['description']}".lower():
                        if endpoint == "department_detail":
                            target = url_for(endpoint, slug=item["slug"])
                        elif endpoint == "services":
                            target = url_for(endpoint, service=item["name"]) + "#request-form"
                        else:
                            target = url_for(endpoint) + "#experiences"
                        results.append({"title": item["name"], "excerpt": item["description"], "url": target})
        return render_template("search.html", title="Search", query=query, results=results)

    @app.route("/api/content/")
    def api_content():
        return jsonify(g.site)

    @app.cli.command("init-db")
    def init_db_command() -> None:
        init_db()
        print("Initialized the LGU Socorro database.")

    with app.app_context():
        init_db()

    return app


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db() -> None:
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS department_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            kind TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'New',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            service TEXT NOT NULL,
            details TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    db.commit()


def load_site_data() -> dict[str, Any]:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    data["departments"] = json.loads((BASE_DIR / "data" / "departments.json").read_text(encoding="utf-8"))
    return data


INQUIRY_KINDS = ("General inquiry", "Appointment request", "Document request", "Feedback")


def verify_csrf() -> None:
    if not secrets.compare_digest(request.form.get("csrf", "").encode("utf-8"), session.get("csrf", "invalid").encode("utf-8")):
        abort(400, description="Your form session expired. Reload the page and try again.")


def find_by_slug(items: list[dict[str, Any]], slug: str) -> dict[str, Any] | None:
    return next((item for item in items if item["slug"] == slug), None)


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

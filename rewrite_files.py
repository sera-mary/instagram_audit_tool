from pathlib import Path

base = Path(__file__).resolve().parent

files = {
    'app.py': '''import json
import sqlite3
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for

from audit_utils import create_audit_payload, rating_label
from config import Config
from forms import AuditForm
from models import Audit, db

load_dotenv()


def get_sqlite_path(database_uri: str) -> Path:
    if database_uri.startswith("sqlite:///"):
        return Path(database_uri.replace("sqlite:///", "")).expanduser()
    raise ValueError("Only sqlite database URIs are supported.")


def migrate_legacy_database(db_path: Path):
    if not db_path.exists():
        return

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audits'")

    if not cursor.fetchone():
        connection.close()
        return

    cursor.execute("PRAGMA table_info(audits)")
    columns = {row[1] for row in cursor.fetchall()}
    legacy_columns = {"business", "instagram", "category", "score", "rating", "created_at"}

    if legacy_columns.issubset(columns) and "business_name" not in columns:
        cursor.execute("ALTER TABLE audits RENAME TO audits_legacy")
        cursor.execute(
            """
            CREATE TABLE audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name VARCHAR(120) NOT NULL,
                instagram_username VARCHAR(80) NOT NULL,
                category VARCHAR(64) NOT NULL,
                business_details TEXT NOT NULL,
                score INTEGER NOT NULL,
                score_breakdown TEXT NOT NULL,
                raw_ratings TEXT NOT NULL,
                strengths TEXT NOT NULL,
                weaknesses TEXT NOT NULL,
                recommendations TEXT NOT NULL,
                services TEXT NOT NULL,
                summary TEXT NOT NULL,
                next_plan TEXT NOT NULL,
                dm TEXT NOT NULL,
                created_at DATETIME NOT NULL
            )
            """
        )
        cursor.execute(
            "INSERT INTO audits (business_name, instagram_username, category, business_details, score, score_breakdown, raw_ratings, strengths, weaknesses, recommendations, services, summary, next_plan, dm, created_at)"
            " SELECT business, instagram, category, 'Imported legacy audit', score, '{}', '{}', 'Legacy audit imported.', 'Legacy audit imported.', 'Legacy audit imported.', 'Legacy audit imported.', 'Legacy audit summary imported.', 'Legacy next action plan imported.', 'Legacy DM imported.', created_at"
            " FROM audits_legacy"
        )
        connection.commit()

    connection.close()


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        sqlite_path = get_sqlite_path(app.config["SQLALCHEMY_DATABASE_URI"])
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        migrate_legacy_database(sqlite_path)
        db.create_all()

    return app


app = create_app()


def get_audit_or_404(audit_id: int):
    audit = Audit.query.get(audit_id)
    if audit is None:
        abort(404)
    return audit


def save_audit(form: AuditForm):
    payload = create_audit_payload(form)
    audit = Audit(
        business_name=form.business_name.data.strip(),
        instagram_username=payload["instagram_username"],
        category=form.category.data,
        business_details=form.business_details.data.strip(),
        score=payload["score"],
        score_breakdown=json.dumps(payload["section_scores"]),
        raw_ratings=json.dumps(payload["raw_ratings"]),
        strengths="\n".join(payload["strengths"]),
        weaknesses="\n".join(payload["weaknesses"]),
        recommendations="\n".join(payload["recommendations"]),
        services="\n".join(payload["services"]),
        summary=payload["summary"],
        next_plan=payload["next_plan"],
        dm=payload["dm"],
        created_at=datetime.utcnow(),
    )
    db.session.add(audit)
    db.session.commit()
    return audit


def populate_form(form: AuditForm, audit: Audit):
    raw_ratings = audit.rating_values()
    form.business_name.data = audit.business_name
    form.instagram_username.data = audit.instagram_username
    form.category.data = audit.category
    form.business_details.data = audit.business_details
    form.bio.data = raw_ratings.get("Bio", "average")
    form.profile_picture.data = raw_ratings.get("Profile Picture", "average")
    form.highlights.data = raw_ratings.get("Highlights", "average")
    form.reels.data = raw_ratings.get("Reels", "average")
    form.branding.data = raw_ratings.get("Branding", "average")
    form.cta.data = raw_ratings.get("CTA", "average")
    form.whatsapp.data = raw_ratings.get("WhatsApp / Order Flow", "available")
    form.posting.data = raw_ratings.get("Posting Consistency", "average")
    form.engagement.data = raw_ratings.get("Engagement", "average")


@app.route("/")
def index():
    form = AuditForm()
    audits = Audit.query.order_by(Audit.created_at.desc()).limit(10).all()
    return render_template("index.html", form=form, audits=audits)


@app.route("/generate", methods=["POST"])
def generate():
    form = AuditForm()
    audits = Audit.query.order_by(Audit.created_at.desc()).limit(10).all()

    if form.validate_on_submit():
        audit = save_audit(form)
        flash("Audit saved successfully.", "success")
        return redirect(url_for("audit_detail", audit_id=audit.id))

    flash("Please fix the errors below and resubmit the form.", "danger")
    return render_template("index.html", form=form, audits=audits)


@app.route("/audits")
def audits_list():
    audits = Audit.query.order_by(Audit.created_at.desc()).all()
    return render_template("audits.html", audits=audits)


@app.route("/audit/<int:audit_id>")
def audit_detail(audit_id: int):
    audit = get_audit_or_404(audit_id)
    return render_template(
        "result.html",
        audit=audit,
        section_scores=audit.score_breakdown_dict(),
        rating=rating_label(audit.score),
    )


@app.route("/audit/<int:audit_id>/edit", methods=["GET", "POST"])
def audit_edit(audit_id: int):
    audit = get_audit_or_404(audit_id)
    form = AuditForm()

    if request.method == "GET":
        populate_form(form, audit)

    if form.validate_on_submit():
        payload = create_audit_payload(form)
        audit.business_name = form.business_name.data.strip()
        audit.instagram_username = payload["instagram_username"]
        audit.category = form.category.data
        audit.business_details = form.business_details.data.strip()
        audit.score = payload["score"]
        audit.score_breakdown = json.dumps(payload["section_scores"])
        audit.raw_ratings = json.dumps(payload["raw_ratings"])
        audit.strengths = "\n".join(payload["strengths"])
        audit.weaknesses = "\n".join(payload["weaknesses"])
        audit.recommendations = "\n".join(payload["recommendations"])
        audit.services = "\n".join(payload["services"])
        audit.summary = payload["summary"]
        audit.next_plan = payload["next_plan"]
        audit.dm = payload["dm"]
        audit.created_at = datetime.utcnow()
        db.session.commit()
        flash("Audit updated successfully.", "success")
        return redirect(url_for("audit_detail", audit_id=audit.id))

    return render_template("edit.html", form=form, audit=audit)


@app.route("/audit/<int:audit_id>/delete", methods=["POST"])
def audit_delete(audit_id: int):
    audit = get_audit_or_404(audit_id)
    db.session.delete(audit)
    db.session.commit()
    flash("Audit deleted successfully.", "warning")
    return redirect(url_for("audits_list"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT)
''',
    'templates/layout.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>B Socio Instagram Audit Tool</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-YSJy0oY1Ugza8e1FoGPvdH2IDgNqdsIquW0y6GVLCEnFjJkJq+CBR7MoGEOd3n6o" crossorigin="anonymous">
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm">
    <div class="container">
        <a class="navbar-brand" href="{{ url_for('index') }}">B Socio Audit v2</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav ms-auto">
                <li class="nav-item"><a class="nav-link" href="{{ url_for('index') }}">Dashboard</a></li>
                <li class="nav-item"><a class="nav-link" href="{{ url_for('audits_list') }}">Saved Audits</a></li>
            </ul>
        </div>
    </div>
</nav>
<main class="container py-5">
    {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
    <div class="mb-4">
        {% for category, message in messages %}
        <div class="alert alert-{{ 'success' if category == 'success' else 'danger' if category == 'danger' else 'warning' }} alert-dismissible fade show" role="alert">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
</main>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/js/bootstrap.bundle.min.js" integrity="sha384-HoA1XmxpE1mgDhkoHUZHZxBhxcx6lmSz+ohP9W/Q27Jx6xgEhb6nDQciwdwqZB1j" crossorigin="anonymous"></script>
<script>
function copyText(elementId) {
    const text = document.getElementById(elementId);
    navigator.clipboard.writeText(text.value).then(() => {
        text.focus();
        text.select();
    });
}
</script>
</body>
</html>''',
    'templates/audits.html': '''{% extends "layout.html" %}

{% block content %}
<div class="card shadow-sm border-0">
    <div class="card-body p-5">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h1 class="h3 mb-1">Saved Audits</h1>
                <p class="text-muted mb-0">Browse and manage your stored reports.</p>
            </div>
            <a href="{{ url_for('index') }}" class="btn btn-primary">New Audit</a>
        </div>
        {% if audits %}
        <div class="table-responsive">
            <table class="table align-middle">
                <thead class="table-light">
                    <tr>
                        <th>Business</th>
                        <th>Category</th>
                        <th>Score</th>
                        <th>Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for audit in audits %}
                    <tr>
                        <td>{{ audit.business_name }}</td>
                        <td>{{ audit.category }}</td>
                        <td>{{ audit.score }}/100</td>
                        <td>{{ audit.created_at.strftime('%Y-%m-%d') }}</td>
                        <td>
                            <a href="{{ url_for('audit_detail', audit_id=audit.id) }}" class="btn btn-sm btn-outline-primary me-1">View</a>
                            <a href="{{ url_for('audit_edit', audit_id=audit.id) }}" class="btn btn-sm btn-outline-secondary me-1">Edit</a>
                            <form action="{{ url_for('audit_delete', audit_id=audit.id) }}" method="POST" class="d-inline">
                                <button type="submit" class="btn btn-sm btn-outline-danger">Delete</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
        <p class="text-muted">No saved audits found yet.</p>
        {% endif %}
    </div>
</div>
{% endblock %}
''',
    'templates/edit.html': '''{% extends "layout.html" %}

{% block content %}
<div class="card shadow-sm border-0">
    <div class="card-body p-5">
        <div class="mb-4">
            <h1 class="h3 mb-1">Edit Audit</h1>
            <p class="text-muted mb-0">Update the audit and regenerate the report.</p>
        </div>
        <form action="{{ url_for('audit_edit', audit_id=audit.id) }}" method="POST" novalidate>
            {{ form.hidden_tag() }}
            <div class="row gx-3">
                <div class="col-md-6 mb-3">
                    <label class="form-label">Business Name</label>
                    {{ form.business_name(class_='form-control' + (' is-invalid' if form.business_name.errors else '')) }}
                    {% for error in form.business_name.errors %}
                    <div class="invalid-feedback">{{ error }}</div>
                    {% endfor %}
                </div>
                <div class="col-md-6 mb-3">
                    <label class="form-label">Instagram Username</label>
                    {{ form.instagram_username(class_='form-control' + (' is-invalid' if form.instagram_username.errors else '')) }}
                    {% for error in form.instagram_username.errors %}
                    <div class="invalid-feedback">{{ error }}</div>
                    {% endfor %}
                </div>
            </div>
            <div class="mb-3">
                <label class="form-label">Business Category</label>
                {{ form.category(class_='form-select' + (' is-invalid' if form.category.errors else '')) }}
                {% for error in form.category.errors %}
                <div class="invalid-feedback">{{ error }}</div>
                {% endfor %}
            </div>
            <div class="mb-4">
                <label class="form-label">Business Details</label>
                {{ form.business_details(class_='form-control' + (' is-invalid' if form.business_details.errors else ''), rows='4') }}
                {% for error in form.business_details.errors %}
                <div class="invalid-feedback">{{ error }}</div>
                {% endfor %}
            </div>
            <div class="row gx-3">
                <div class="col-md-4 mb-3">
                    <label class="form-label">Bio</label>
                    {{ form.bio(class_='form-select') }}
                </div>
                <div class="col-md-4 mb-3">
                    <label class="form-label">Profile Picture</label>
                    {{ form.profile_picture(class_='form-select') }}
                </div>
                <div class="col-md-4 mb-3">
                    <label class="form-label">Highlights</label>
                    {{ form.highlights(class_='form-select') }}
                </div>
            </div>
            <div class="row gx-3">
                <div class="col-md-4 mb-3">
                    <label class="form-label">Reels</label>
                    {{ form.reels(class_='form-select') }}
                </div>
                <div class="col-md-4 mb-3">
                    <label class="form-label">Branding</label>
                    {{ form.branding(class_='form-select') }}
                </div>
                <div class="col-md-4 mb-3">
                    <label class="form-label">CTA</label>
                    {{ form.cta(class_='form-select') }}
                </div>
            </div>
            <div class="row gx-3">
                <div class="col-md-4 mb-3">
                    <label class="form-label">WhatsApp / Order Flow</label>
                    {{ form.whatsapp(class_='form-select') }}
                </div>
                <div class="col-md-4 mb-3">
                    <label class="form-label">Posting Consistency</label>
                    {{ form.posting(class_='form-select') }}
                </div>
                <div class="col-md-4 mb-3">
                    <label class="form-label">Engagement</label>
                    {{ form.engagement(class_='form-select') }}
                </div>
            </div>
            <div class="d-flex justify-content-between mt-4">
                <a href="{{ url_for('audit_detail', audit_id=audit.id) }}" class="btn btn-outline-secondary">Cancel</a>
                {{ form.submit(class_='btn btn-primary') }}
            </div>
        </form>
    </div>
</div>
{% endblock %}
'''
}

for path, content in files.items():
    p = base / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')

print('files_written')

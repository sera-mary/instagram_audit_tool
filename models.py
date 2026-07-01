import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(120), nullable=False)
    instagram_username = db.Column(db.String(80), nullable=False)
    category = db.Column(db.String(64), nullable=False)
    business_details = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    score_breakdown = db.Column(db.Text, nullable=False)
    raw_ratings = db.Column(db.Text, nullable=False)
    strengths = db.Column(db.Text, nullable=False)
    weaknesses = db.Column(db.Text, nullable=False)
    recommendations = db.Column(db.Text, nullable=False)
    services = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    next_plan = db.Column(db.Text, nullable=False)
    dm = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def strengths_list(self):
        return [item for item in self.strengths.splitlines() if item]

    def weaknesses_list(self):
        return [item for item in self.weaknesses.splitlines() if item]

    def recommendations_list(self):
        return [item for item in self.recommendations.splitlines() if item]

    def services_list(self):
        return [item for item in self.services.splitlines() if item]

    def score_breakdown_dict(self):
        try:
            return json.loads(self.score_breakdown or "{}")
        except json.JSONDecodeError:
            return {}

    def rating_values(self):
        try:
            return json.loads(self.raw_ratings or "{}")
        except json.JSONDecodeError:
            return {}

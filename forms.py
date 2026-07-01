from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Regexp

CATEGORY_CHOICES = [
    ("", "Choose category"),
    ("Restaurant", "Restaurant"),
    ("Cafe", "Cafe"),
    ("Salon", "Salon"),
    ("Boutique", "Boutique"),
    ("Gym", "Gym"),
    ("Clinic", "Clinic"),
    ("Creator", "Creator"),
    ("Local Business", "Local Business"),
    ("Other", "Other"),
]

RATING_CHOICES = [
    ("excellent", "Excellent"),
    ("average", "Average"),
    ("needs_improvement", "Needs Improvement"),
]


class AuditForm(FlaskForm):
    business_name = StringField(
        "Business Name",
        validators=[
            DataRequired(message="Business name is required."),
            Length(max=120),
        ],
    )

    instagram_username = StringField(
        "Instagram Username",
        validators=[
            DataRequired(message="Instagram username is required."),
            Regexp(
                r"^@?[A-Za-z0-9_.]{1,30}$",
                message="Enter a valid Instagram username with letters, numbers, dots, or underscores.",
            ),
            Length(max=30),
        ],
    )

    category = SelectField(
        "Business Category",
        choices=CATEGORY_CHOICES,
        validators=[DataRequired(message="Please select a business category.")],
    )

    business_details = TextAreaField(
        "Business Details",
        validators=[
            DataRequired(message="Describe the business, audience, and Instagram goals."),
            Length(max=400),
        ],
    )

    bio = SelectField("Bio", choices=RATING_CHOICES, validators=[DataRequired()])
    profile_picture = SelectField("Profile Picture", choices=RATING_CHOICES, validators=[DataRequired()])
    highlights = SelectField("Highlights", choices=RATING_CHOICES, validators=[DataRequired()])
    reels = SelectField("Reels", choices=RATING_CHOICES, validators=[DataRequired()])
    branding = SelectField("Branding", choices=RATING_CHOICES, validators=[DataRequired()])
    cta = SelectField("CTA", choices=RATING_CHOICES, validators=[DataRequired()])
    whatsapp = SelectField(
        "WhatsApp / Order Flow",
        choices=[("available", "Available"), ("not_available", "Not Available")],
        validators=[DataRequired()],
    )
    posting = SelectField("Posting Consistency", choices=RATING_CHOICES, validators=[DataRequired()])
    engagement = SelectField("Engagement", choices=RATING_CHOICES, validators=[DataRequired()])
    submit = SubmitField("Generate Audit")

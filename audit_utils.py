from datetime import datetime

SECTIONS = {
    "Bio": 10,
    "Profile Picture": 10,
    "Highlights": 10,
    "Reels": 15,
    "Branding": 15,
    "CTA": 10,
    "WhatsApp / Order Flow": 10,
    "Posting Consistency": 10,
    "Engagement": 10,
}

RATING_SCORE = {
    "excellent": 10,
    "average": 6,
    "needs_improvement": 2,
    "available": 10,
    "not_available": 2,
}

SERVICE_TAGS = {
    "Branding": "Branding",
    "Digital Marketing": "Digital Marketing",
    "Social Media Management": "Social Media Management",
    "Website Development": "Website Development",
    "SEO": "SEO",
    "ERP": "ERP",
    "QR Menu": "QR Menu",
}

CATEGORY_QR = {"Restaurant", "Cafe"}


def normalize_username(username: str) -> str:
    username = username.strip()
    if not username:
        return "@profile"
    return username if username.startswith("@") else f"@{username}"


def build_section_scores(form_data):
    raw_values = {
        "Bio": form_data.bio.data,
        "Profile Picture": form_data.profile_picture.data,
        "Highlights": form_data.highlights.data,
        "Reels": form_data.reels.data,
        "Branding": form_data.branding.data,
        "CTA": form_data.cta.data,
        "WhatsApp / Order Flow": form_data.whatsapp.data,
        "Posting Consistency": form_data.posting.data,
        "Engagement": form_data.engagement.data,
    }

    section_scores = {}
    for section, weight in SECTIONS.items():
        rating_key = raw_values[section]
        rating_value = RATING_SCORE.get(rating_key, 2)
        section_scores[section] = int((rating_value / 10) * weight)

    return section_scores, raw_values


def generate_weaknesses_and_strengths(section_scores):
    strengths = []
    weaknesses = []
    for section, score in section_scores.items():
        if score >= (SECTIONS[section] * 0.8):
            strengths.append(section)
        else:
            weaknesses.append(section)
    return strengths, weaknesses


def build_recommendations(weaknesses, category):
    recommendations = []
    services = set()

    mapping = {
        "Bio": ("Sharpen the business bio with a clear value proposition and service focus.", "Digital Marketing"),
        "Profile Picture": ("Use a high-quality logo or brand image to make the profile memorable.", "Branding"),
        "Highlights": ("Turn highlights into a story archive that answers common customer questions.", "Social Media Management"),
        "Reels": ("Share short, consistent reels that show products, services, and behind-the-scenes moments.", "Social Media Management"),
        "Branding": ("Align colors, fonts, and captions for a stronger brand identity.", "Branding"),
        "CTA": ("Add a clear call to action in the bio, captions, and story links.", "Digital Marketing"),
        "WhatsApp / Order Flow": ("Enable direct messaging or order flow to reduce friction for customers.", "ERP"),
        "Posting Consistency": ("Publish on a regular schedule to keep followers engaged and the algorithm active.", "Social Media Management"),
        "Engagement": ("Reply to comments, messages, and story replies to turn followers into customers.", "Digital Marketing"),
    }

    for issue in weaknesses:
        message, service = mapping.get(issue, (None, None))
        if message and message not in recommendations:
            recommendations.append(message)
        if service:
            services.add(service)

    if category in CATEGORY_QR:
        services.add(SERVICE_TAGS["QR Menu"])
        if "Create a scannable QR menu for fast customer ordering." not in recommendations:
            recommendations.append("Create a scannable QR menu for fast customer ordering.")

    if "Branding" in services and "Website Development" not in services:
        services.add(SERVICE_TAGS["Website Development"])

    if len(services) < 3:
        services.add(SERVICE_TAGS["SEO"])

    return sorted(services), recommendations


def rating_label(score: int) -> str:
    if score >= 90:
        return "⭐⭐⭐⭐⭐ Excellent"
    if score >= 75:
        return "⭐⭐⭐⭐ Very Good"
    if score >= 60:
        return "⭐⭐⭐ Good"
    if score >= 40:
        return "⭐⭐ Average"
    return "⭐ Needs Improvement"


def generate_audit_text(business_name, instagram, category, business_details, strengths, weaknesses, recommendations, services, score):
    strengths_text = ", ".join(strengths) if strengths else "consistent content and brand positioning"
    weaknesses_text = ", ".join(weaknesses) if weaknesses else "no major structural issues"
    improvements_text = (
        ". ".join(recommendations) if recommendations else "Keep raising the profile through consistent storytelling and user focus."
    )

    summary = (
        f"{business_name} is a {category} on Instagram {instagram}. "
        f"The audit score is {score} out of 100. "
        f"Strengths include {strengths_text}. "
        f"The audit identified {weaknesses_text}. "
        f"Recommended improvements are: {improvements_text}"
    )

    next_plan = (
        "Next, focus on stronger profile messaging, regular content, and a smoother WhatsApp/order flow. "
        "Then pitch the brand with clear service offerings and conversion pathways."
    )

    dm = (
        f"Hi {business_name}, I reviewed your Instagram profile {instagram} and created a quick audit. "
        f"The current score is {score}/100, with opportunities in {weaknesses_text}. "
        f"I recommend improving your bio, branding, and content consistency, and I can support this with B Socio services like {', '.join(services)}. "
        f"Let me know if you want a tailored growth plan."
    )

    return summary, next_plan, dm


def create_audit_payload(form):
    username = normalize_username(form.instagram_username.data)
    section_scores, raw_ratings = build_section_scores(form)
    strength_list, weakness_list = generate_weaknesses_and_strengths(section_scores)
    services, recommendations = build_recommendations(weakness_list, form.category.data)
    score = sum(section_scores.values())

    summary, next_plan, dm = generate_audit_text(
        form.business_name.data,
        username,
        form.category.data,
        form.business_details.data,
        strength_list,
        weakness_list,
        recommendations,
        services,
        score,
    )

    return {
        "instagram_username": username,
        "score": score,
        "section_scores": section_scores,
        "raw_ratings": raw_ratings,
        "strengths": strength_list,
        "weaknesses": weakness_list,
        "recommendations": recommendations,
        "services": services,
        "summary": summary,
        "next_plan": next_plan,
        "dm": dm,
    }

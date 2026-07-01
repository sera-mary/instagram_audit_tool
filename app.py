from flask import Flask, render_template, request

app = Flask(__name__)


def parse_list(raw_value):
    if not raw_value:
        return []

    items = [item.strip() for item in raw_value.replace("\n", ",").split(",")]
    return [item for item in items if item]


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    business = request.form.get('business', 'Your Business')
    instagram = request.form.get('instagram', '@yourprofile')
    category = request.form.get('category', 'Other')
    business_details = request.form.get('business_details', 'No additional business context provided.')
    weak_points = parse_list(request.form.get('weak_points', ''))
    suggestions = parse_list(request.form.get('suggestions', ''))

    bio = request.form.get('bio', 'Average')
    highlights = request.form.get('highlights', 'Average')
    reels = request.form.get('reels', 'Average')
    branding = request.form.get('branding', 'Average')
    cta = request.form.get('cta', 'Average')
    whatsapp = request.form.get('whatsapp', 'Available')

    score = 100
    weaknesses = []

    if bio == "Needs Improvement":
        score -= 10
        weaknesses.append("Improve Bio")

    if highlights == "Needs Improvement":
        score -= 15
        weaknesses.append("Create Better Highlights")

    if reels == "Needs Improvement":
        score -= 20
        weaknesses.append("Post More Engaging Reels")

    if branding == "Needs Improvement":
        score -= 20
        weaknesses.append("Improve Branding")

    if cta == "Needs Improvement":
        score -= 15
        weaknesses.append("Add a Clear Call To Action")

    if whatsapp == "Not Available":
        score -= 20
        weaknesses.append("Enable WhatsApp / Order Flow")

    if weak_points:
        score -= min(10 + len(weak_points) * 2, 25)

    services = []

    if branding == "Needs Improvement":
        services.append("Branding")

    if reels == "Needs Improvement":
        services.append("Social Media Marketing")

    if whatsapp == "Not Available":
        services.append("WhatsApp Integration")

    if cta == "Needs Improvement":
        services.append("Digital Marketing")

    if weak_points:
        services.append("Content Strategy")

    if score >= 90:
        rating = "⭐⭐⭐⭐⭐ Excellent"
    elif score >= 75:
        rating = "⭐⭐⭐⭐ Very Good"
    elif score >= 60:
        rating = "⭐⭐⭐ Good"
    elif score >= 40:
        rating = "⭐⭐ Average"
    else:
        rating = "⭐ Needs Improvement"

    if weak_points:
        weakness_text = ", ".join(weak_points)
    else:
        weakness_text = "No major weaknesses identified"

    if suggestions:
        suggestion_text = ", ".join(suggestions)
    else:
        suggestion_text = "Add clearer positioning, content themes, and conversion steps"

    summary = (
        f"{business} operates in the {category} space and is building a presence on Instagram "
        f"{instagram}. {business_details} The main audit themes are {weakness_text}. "
        f"Suggested next steps are {suggestion_text}."
    )

    dm = (
        f"Hi {business}, we reviewed your Instagram profile and found several opportunities to improve "
        f"your online presence. Our team at B Socio can help you with {', '.join(services) or 'profile growth'} ."
    )

    return render_template(
        "result.html",
        business=business,
        instagram=instagram,
        category=category,
        business_details=business_details,
        score=score,
        rating=rating,
        weaknesses=weaknesses + weak_points,
        services=services,
        summary=summary,
        dm=dm,
        suggestions=suggestions,
    )


if __name__ == "__main__":
    app.run(debug=True)
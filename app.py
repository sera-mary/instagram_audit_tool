from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    business = request.form['business']
    instagram = request.form['instagram']
    weak_points = request.form['weak_points']
    suggestions = request.form['suggestions']

    summary = f"{business}'s Instagram account ({instagram}) needs improvement. The weak points are {weak_points}. By following these suggestions: {suggestions}, the account can improve engagement and reach."

    return render_template(
        'result.html',
        business=business,
        instagram=instagram,
        weak_points=weak_points,
        suggestions=suggestions,
        summary=summary
    )

if __name__ == "__main__":
    app.run(debug=True)
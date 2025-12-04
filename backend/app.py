from flask import Flask, render_template, request, jsonify
from analyzer import analyze_reddit_post
import os

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json or {}
    url = data.get("url") or request.form.get("url")
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        result = analyze_reddit_post(url)
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

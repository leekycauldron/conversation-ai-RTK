from flask import Flask, request, jsonify
from datetime import datetime
from uploader import main

app = Flask(__name__)

FACTS_FILE = "facts.txt"

@app.route("/")
def home():
    return "Fact-saving API is running."

@app.route("/save-fact", methods=["POST"])
def save_fact():
    data = request.get_json()
    fact = data.get("fact")

    if not fact:
        return jsonify({"error": "Missing fact"}), 400

    timestamp = datetime.utcnow().isoformat()
    with open(FACTS_FILE, "a") as f:
        f.write(f"{timestamp} | {fact}\n")
    main()
    return jsonify({"status": "success", "message": f"Fact saved: {fact}"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

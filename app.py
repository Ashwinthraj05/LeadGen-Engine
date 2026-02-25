from flask import Flask, render_template, request, jsonify, send_file
from threads.job_manager import start_job, jobs

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return render_template("dashboard.html")   # ✅ FIXED


@app.route("/start", methods=["POST"])
def start():
    cities_input = request.form.get("cities")
    categories_input = request.form.get("categories")

    cities = [c.strip() for c in cities_input.split(",")]
    categories = [c.strip() for c in categories_input.split(",")]

    job_id = start_job(cities, categories)

    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)

    if not job:
        return jsonify({"error": "Invalid Job ID"})

    return jsonify(job)


@app.route("/download/<job_id>")
def download(job_id):
    job = jobs.get(job_id)

    if job and job["status"] == "completed":
        return send_file(job["file"], as_attachment=True)

    return "File not ready yet."


if __name__ == "__main__":
    print("Starting Flask Server...")
    app.run(debug=True)

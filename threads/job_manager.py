import threading
import uuid

from core.orchestrator import run_global_scraper

# Store jobs in memory
jobs = {}


def start_job(cities, categories):
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "file": None
    }

    thread = threading.Thread(
        target=run_job,
        args=(job_id, cities, categories)
    )

    thread.start()

    return job_id


def run_job(job_id, cities, categories):
    try:
        file_path = run_global_scraper(
            cities=cities,
            categories=categories
        )

        jobs[job_id].update({
            "status": "completed",
            "progress": 100,
            "file": file_path
        })

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

import json
import os
from datetime import datetime

LOGS_DIR = "logs"
EXPERIMENTS_FILE = os.path.join(LOGS_DIR, "experiments.json")

# Ensure logs directory exists
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

def log_experiment(run_id: str, task: str, model_name: str, output: str, scores: dict, latency: float, status: str = "success", model_version: str = "latest"):
    """
    Appends a structured experiment payload into the experiments.json file.
    """
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "run_id": str(run_id),
        "status": status,
        "input_task": task,
        "model_used": model_name,
        "model_version": model_version,
        "output": output,
        "evaluation_scores": scores,
        "latency_ms": latency
    }
    
    # Simple file append log (for true production we would use logging native handlers or ELK)
    try:
        with open(EXPERIMENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        print(f"[LoggerError] Failed to write to {EXPERIMENTS_FILE}: {e}")

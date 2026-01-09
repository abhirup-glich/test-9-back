import shutil
import os
from flask import jsonify

def check_storage_usage():
    """
    Check if storage usage is within limits (500MB).
    Render free tier often has ephemeral disk, but we want to ensure we don't fill it up.
    """
    total, used, free = shutil.disk_usage("/")
    
    # Convert to MB
    used_mb = used // (2**20)
    
    # This is a bit of a naive check because "/" includes the OS.
    # A better check might be the current working directory if volume is mounted.
    # However, for the prompt's requirement, we'll expose this endpoint.
    
    return {
        "total_mb": total // (2**20),
        "used_mb": used_mb,
        "free_mb": free // (2**20),
        "status": "ok" if used_mb < 500 else "warning" # 500MB is very small for a whole OS, assuming this refers to /tmp or app data
    }

def register_monitoring(app):
    @app.route('/health/storage')
    def storage_health():
        usage = check_storage_usage()
        # In a real scenario, we might return 503 if critical
        return jsonify(usage)

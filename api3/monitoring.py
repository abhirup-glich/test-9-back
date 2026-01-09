import shutil
from flask import jsonify

def check_storage_usage():
    total, used, free = shutil.disk_usage("/")
    return {
        "total_mb": total // (2**20),
        "used_mb": used // (2**20),
        "free_mb": free // (2**20)
    }

def register_monitoring(app):
    @app.route('/health/storage')
    def storage_health():
        return jsonify(check_storage_usage())

from flask import Flask
import os
import sys

# Fix for Windows socket error
if sys.platform == "win32":
    import asyncio
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except:
        pass

from app.routes.home import home_bp
from app.routes.upload import upload_bp
from app.routes.chat import chat_bp

app = Flask(__name__)

# Configuration
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max upload

# Register blueprints
app.register_blueprint(home_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(chat_bp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    
    # For Windows, use threaded=False to avoid socket issues
    if sys.platform == "win32":
        print(f"🚀 Starting DocuMind AI on http://localhost:{port}")
        app.run(host="127.0.0.1", port=port, debug=False, threaded=False, use_reloader=False)
    else:
        app.run(host="0.0.0.0", port=port, debug=debug)
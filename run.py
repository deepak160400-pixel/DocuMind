from flask import Flask

from app.routes.home import home_bp
from app.routes.upload import upload_bp
from app.routes.chat import chat_bp

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "uploads"

app.register_blueprint(home_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(chat_bp)

if __name__ == "__main__":
    app.run(debug=True)
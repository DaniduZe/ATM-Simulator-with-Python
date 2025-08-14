import os
from flask import Flask
from dotenv import load_dotenv
from routes.customer_router import customer_bp

load_dotenv()  # Load variables from .env

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback_secret")  # JWT secret key

# Register blueprints
app.register_blueprint(customer_bp)

if __name__ == "__main__":
    app.run(debug=True)

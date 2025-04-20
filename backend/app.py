from flask import Flask, jsonify
from flask_cors import CORS
import ssl

from config.settings import (
    FLASK_SECRET_KEY,
    CORS_ORIGINS,
    CORS_HEADERS,
    CORS_METHODS
)
from config.database import Database

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# Configure CORS
CORS(app, 
     origins=CORS_ORIGINS,
     allow_headers=CORS_HEADERS,
     methods=CORS_METHODS,
     supports_credentials=True)

# Initialize database and ensure connection
db = Database.get_instance()
if not db.ensure_connected():
    print("Warning: Failed to establish database connection. Some features may not work.")

# Import blueprints after database initialization
from blueprints.auth import auth_bp
from blueprints.summary import summary_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(summary_bp)

@app.route('/')
def index():
    if not db.is_connected():
        return jsonify({
            "status": "degraded",
            "message": "Database connection unavailable"
        }), 503
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('../frontend/cert.pem', '../frontend/key.pem')
    app.run(host='0.0.0.0', port=5000, ssl_context=context, debug=True)

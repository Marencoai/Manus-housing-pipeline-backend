import os
import sys
from dotenv import load_dotenv
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

load_dotenv()

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.database import db
from src.routes.projects import projects_bp
from src.routes.clients import clients_bp
from src.routes.applications import applications_bp
from src.routes.funding_sources import funding_sources_bp
from src.routes.sharepoint import sharepoint_bp
# from src.routes.ai_chat import ai_chat_bp  # Temporarily disabled for deployment
from src.routes.time_tracking import time_tracking_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'housing-pipeline-pro-secret-key-2025')

# Enable CORS for all routes with specific origins
CORS(app, origins=["*", "https://manus-housing-pipeline-frontend-v2.vercel.app", "https://manus-housing-pipeline-frontend.vercel.app"], 
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'])

# Register blueprints
app.register_blueprint(projects_bp, url_prefix='/api/projects')
app.register_blueprint(clients_bp, url_prefix='/api/clients')
app.register_blueprint(applications_bp, url_prefix='/api/applications')
app.register_blueprint(funding_sources_bp, url_prefix='/api/funding-sources')
app.register_blueprint(sharepoint_bp, url_prefix='/api/sharepoint')
# app.register_blueprint(ai_chat_bp, url_prefix='/api/ai')  # Temporarily disabled
app.register_blueprint(time_tracking_bp, url_prefix='/api/time-tracking')

# Database configuration
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Railway PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local SQLite fallback
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    # Import and run seed data
    from src.models.seed_data import seed_database
    seed_database()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


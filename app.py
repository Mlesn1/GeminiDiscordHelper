"""
Flask web application for the Discord bot hosting on PythonAnywhere.
This serves as a simple web interface and keeps the bot alive.
"""
import os
import logging
from flask import Flask, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

with app.app_context():
    # Import the models here to avoid circular imports
    import models  # noqa: F401
    
    # Create tables if they don't exist
    db.create_all()
    logger.info("Database tables created or verified")

@app.route('/')
def index():
    """Homepage route that displays bot status and info."""
    import datetime
    import platform
    from flask import render_template
    
    # Get the bot status from our status endpoint
    status_info = {
        "status": "Online",
        "uptime": "Unknown",
        "servers": "N/A",
    }
    
    # Determine hosting environment
    hosting_env = "Replit"
    if "PYTHONANYWHERE_DOMAIN" in os.environ:
        hosting_env = "PythonAnywhere"
    
    # Try to get actual status if available
    try:
        # This would be replaced with actual bot status info in a real app
        # For now, we'll use some dummy data
        pass
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        
    return render_template(
        'index.html',
        bot_status=status_info.get("status", "Unknown"),
        bot_uptime=status_info.get("uptime", None),
        hosting_env=hosting_env
    )

@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "ok"})

@app.route('/api/status')
def status():
    """API endpoint that returns the bot status."""
    import platform
    
    # Determine hosting environment
    hosting_env = "Replit"
    if "PYTHONANYWHERE_DOMAIN" in os.environ:
        hosting_env = "PythonAnywhere"
    
    # In a real application, we would check the actual bot status
    # For now, we'll use static data
    return jsonify({
        "status": "online",
        "uptime": "unknown",  # This would be calculated in a real app
        "servers": "N/A",     # Number of servers the bot is in
        "version": "1.0.0",
        "hosting": hosting_env,
        "python_version": platform.python_version(),
        "system": platform.system()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
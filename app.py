"""
Flask web application for the Discord bot hosting on PythonAnywhere.
This serves as a simple web interface and keeps the bot alive.
"""
import os
import logging
from flask import Flask, jsonify, Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

@app.route('/')
def index():
    """Homepage route that displays bot status and info."""
    from flask import render_template
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "ok"})

@app.route('/api/status')
def status():
    """API endpoint that returns the bot status."""
    # In a real application, we would check the actual bot status
    return jsonify({
        "status": "online",
        "uptime": "unknown",  # This would be calculated in a real app
        "servers": "N/A",     # Number of servers the bot is in
        "version": "1.0.0"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
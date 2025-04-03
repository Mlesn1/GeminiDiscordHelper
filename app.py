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
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gemini Discord Bot</title>
        <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body data-bs-theme="dark">
        <div class="container mt-5">
            <h1 class="text-center">Gemini Discord Bot</h1>
            <p class="text-center">A Discord bot powered by Google's Gemini 1.5 AI</p>
            
            <div class="row mt-5">
                <div class="col-md-6 offset-md-3">
                    <div class="card">
                        <div class="card-header">
                            Bot Status
                        </div>
                        <div class="card-body">
                            <p>This bot is running and ready to handle Discord commands.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return Response(html, mimetype='text/html')

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
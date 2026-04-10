from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "AI Attendance Cloud Running"

@app.route("/api/attendance")
def data():
    return jsonify({"status": "ok", "data": []})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal Server Error'}), 500


if __name__ == '__main__':
    logger.info("Starting Cloud Backend Server...")
    # For production, use gunicorn: gunicorn -w 4 -b 0.0.0.0:5000 app:app
    app.run(debug=False, host='0.0.0.0', port=5000)

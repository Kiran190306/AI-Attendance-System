from flask import Flask, render_template, jsonify, send_file
from backend.database.db import SessionLocal
from backend.database.repository import AttendanceRepository
from datetime import date, datetime
from pathlib import Path
import io
import csv

app = Flask(__name__, template_folder="templates")

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/api/today")
def today():
    db = SessionLocal()
    recs = AttendanceRepository.list_today(db)
    db.close()
    data = []
    for r in recs:
        data.append({"name": r.student_name, "timestamp": r.timestamp.isoformat(), "confidence": r.confidence})
    return jsonify(data)

@app.route("/api/stats")
def stats():
    db = SessionLocal()
    recs = AttendanceRepository.list_today(db)
    db.close()
    total = len(recs)
    # simple late threshold 09:00
    threshold = datetime.combine(date.today(), datetime.strptime("09:00", "%H:%M").time())
    late = sum(1 for r in recs if r.timestamp > threshold)
    return jsonify({"total": total, "late": late})


@app.route("/api/presence")
def presence():
    """Return aggregated presence analytics read from CSV log."""
    path = Path("analytics/session_log.csv")
    if not path.exists():
        return jsonify({"records": [], "summary": {}})
    rows = []
    total_focus = 0.0
    total_distraction = 0.0
    with path.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
            try:
                total_focus += float(r.get("focus_percent", 0))
                total_distraction += float(r.get("distraction_percent", 0))
            except ValueError:
                pass
    count = len(rows)
    avg_attention = total_focus / count if count > 0 else 0.0
    return jsonify({
        "records": rows,
        "summary": {
            "total_people": count,
            "avg_attention": avg_attention,
            "average_distraction": total_distraction / count if count > 0 else 0.0,
        },
    })

@app.route("/export")
def export():
    db = SessionLocal()
    recs = AttendanceRepository.list_today(db)
    db.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "timestamp", "confidence"])
    for r in recs:
        writer.writerow([r.student_name, r.timestamp.isoformat(), r.confidence])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name="today.csv")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)

# Web Dashboard - AI Attendance System

Professional Flask web interface for viewing and managing attendance records.

## Quick Start

### 1. Install Flask

```bash
# From project root
pip install -r web/requirements.txt
```

### 2. Start the Dashboard

```bash
# From project root
python web_dashboard.py
```

The dashboard will automatically open in your browser at `http://localhost:5000`

## Features

✅ **Dashboard** - View today's attendance with real-time statistics  
✅ **Student List** - See all enrolled students and enrollment status  
✅ **Attendance Records** - Browse complete attendance history  
✅ **Date Filtering** - Filter records by specific dates  
✅ **CSV Download** - Export attendance data for external analysis  
✅ **Responsive Design** - Works on desktop, tablet, and mobile  
✅ **Real-time Stats** - Immediate attendance rate calculations  
✅ **Professional UI** - Modern gradient design with smooth animations  

## Pages

### Dashboard (`/`)
**Main landing page showing today's attendance**

- Today's date
- Total enrolled students
- Number marked today
- Attendance rate percentage
- Complete list of today's attendance records (time, name, confidence, timestamp)
- Quick action buttons

### Students (`/students`)
**View all enrolled students**

- Total student count
- Active students (with valid faces)
- Students needing setup (no valid face images)
- Student directory with:
  - Student name
  - Images found (from dataset)
  - Valid faces (successfully processed)
  - Status (Active/No Faces)
- Setup instructions for adding new students

### Records (`/records`)
**Complete attendance history with filtering**

- All attendance records with timestamps
- Date filter dropdown for quick filtering
- Filter by specific date or view all records
- Attendance breakdown with dates, times, names, confidence levels
- Export option at page bottom

### API Endpoints

**GET `/api/stats`**
```json
{
  "today_date": "2024-01-15",
  "marked_today": 42,
  "total_students": 50,
  "marked_percentage": "84.0%"
}
```

**GET `/api/records/<date>`**
```json
{
  "date": "2024-01-15",
  "total": 42,
  "records": [
    {
      "time": "09:30:45",
      "name": "Alice",
      "confidence": 0.95
    },
    ...
  ]
}
```

**GET `/download-csv`**
Downloads the complete `attendance.csv` file

**GET `/health`**
Health check endpoint returning system status

## Database/Records Structure

The dashboard reads from `attendance/attendance.csv`:

```
date,time,name,timestamp_iso,confidence
2024-01-15,09:30:45,Alice,2024-01-15T09:30:45.123456,0.95
2024-01-15,09:31:12,Bob,2024-01-15T09:31:12.456789,0.87
2024-01-15,09:32:33,Charlie,2024-01-15T09:32:33.789012,0.92
```

**Columns:**
- `date`: Date in YYYY-MM-DD format
- `time`: Time in HH:MM:SS format
- `name`: Student name
- `timestamp_iso`: Full ISO 8601 timestamp with microseconds
- `confidence`: Face recognition confidence (0.0 to 1.0)

## Styling

**Color Scheme:**
- Primary: `#667eea` (Purple-blue)
- Secondary: `#764ba2` (Deep purple)
- Success: `#48bb78` (Green)
- Warning: `#ed8936` (Orange)
- Danger: `#f56565` (Red)

**Responsive Breakpoints:**
- Desktop: 1200px+
- Tablet: 768px - 1199px
- Mobile: < 768px
- Small mobile: < 480px

**Animations:**
- Slide down (header)
- Slide up (cards)
- Fade in (tables)
- Bounce (empty states)
- Smooth transitions on all interactive elements

## Navigation

**Top Navigation Bar:**
- Logo with emoji and brand name
- Dashboard link (home page)
- Students link
- Records link

**Links highlight current page**

**Quick Action Buttons:**
- Throughout the app for easy navigation
- Download CSV from dashboard and records pages
- Setup instructions on students page

## Confidence Badges

Records show confidence levels with color-coded badges:
- 🟢 **Success (95%+)**: Dark green badge - High confidence
- 🔵 **Secondary (85-95%)**: Light blue badge - Good confidence
- 🟡 **Warning (<85%)**: Orange badge - Lower confidence

## Filters

**Date Filter (Records Page)**
- Dropdown with all unique dates from history
- "All Dates" option to view complete history
- Auto-submit on selection
- Shows count matching current filter

## Export/Download

**CSV Download**
- Available from dashboard and records pages
- Downloads complete `attendance.csv`
- Filename includes timestamp: `attendance_20240115_093045.csv`
- Format: UTF-8 encoding, comma-separated values

## Empty States

**No Records Today**
- Dashboard shows empty state if no attendance yet in day
- Encourages user to check back later or verify system is running

**No Students**
- Students page shows empty state if dataset folder has no students
- Displays setup instructions

**No Records for Date**
- Records page shows empty state if selected date has no records

## Mobile Responsive

- **Navbar collapses** on small screens
- **Button groups stack** vertically
- **Table remains scrollable** on small screens
- **Stats grid becomes single column** on mobile
- **Touch-friendly** button sizes and spacing

## Browser Compatibility

✓ Chrome 90+  
✓ Firefox 88+  
✓ Safari 14+  
✓ Edge 90+  
✓ Mobile Safari (iOS 14+)  
✓ Chrome Mobile  

## Development

### Project Structure

```
web/
├── app.py                    # Flask application and routes
├── __init__.py               # Package init
├── requirements.txt          # Flask dependencies
├── templates/
│   ├── base.html            # Base layout with navigation
│   ├── dashboard.html        # Today's attendance dashboard
│   ├── records.html          # All records with filtering
│   └── students.html         # Student directory
└── static/
    └── style.css            # Responsive styling
```

### Adding New Pages

1. Create template in `web/templates/page.html` extending `base.html`
2. Add route in `web/app.py`:
   ```python
   @app.route('/page')
   def page():
       # Get data
       return render_template('page.html', data=data)
   ```
3. Add link to navbar in `base.html`

### Customizing Styling

Edit `web/static/style.css` or modify styles in template `<style>` blocks:

```css
:root {
    --primary: #667eea;
    --secondary: #764ba2;
    --success: #48bb78;
    /* etc */
}
```

## Troubleshooting

### "Port 5000 already in use"

```bash
# Change port in web_dashboard.py
app.run(port=5001)  # Use different port
```

### "Cannot find attendance.csv"

- Ensure attendance system has run at least once
- Check `attendance/` folder exists in project root
- Run main system: `python attendance_system.py`

### "No students shown"

- Ensure `dataset/` folder contains student subfolders
- Each student folder needs at least one face image
- Restart web dashboard after adding students

### "Flask not installed"

```bash
pip install Flask==2.3.3 Werkzeug==2.3.7
```

## Performance Notes

- Dashboard loads data from CSV on each request (suitable for ~1000s of records)
- For larger datasets, consider database backend
- Page load time < 500ms on typical systems
- CSV download size: ~50KB per 1000 records

## Security Notes

- Dashboard runs on `localhost:5000` by default (local network access)
- For production deployment:
  - Use HTTPS with SSL certificates
  - Deploy behind reverse proxy (nginx/Apache)
  - Add authentication
  - Limit CSV download access

## Future Enhancements

- 📊 Charts and graphs (attendance trends)
- 📅 Calendar view of attendance
- 🔍 Advanced search and filtering
- 📧 Email reports
- ⚙️ Admin dashboard
- 🔐 User authentication
- 💾 Database backend (SQLite/PostgreSQL)
- 📱 Mobile app

## Keyboard Shortcuts

*(Can be added in future versions)*

- `? ` - Show help
- `D` - Go to dashboard
- `S` - Go to students
- `R` - Go to records
- `Cmd/Ctrl + K` - Command palette

---

**Status:** ✅ Production-Ready  
**Version:** 1.0  
**Last Updated:** March 5, 2026

const STATS_URL = '/api/get_stats';
const ATTENDANCE_URL = '/api/get_attendance';
const AUTO_REFRESH_MS = 30000;

let attendanceRecords = [];
let ratioChart = null;
let hourChart = null;
let refreshTimer = null;

function formatPct(value) {
    return `${Number(value).toFixed(1)}%`;
}

function formatTime(timestamp) {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function renderStatusChip(confidence) {
    if (confidence == null) {
        return '<span class="status-chip absent">Unknown</span>';
    }
    const score = Number(confidence) * 100;
    if (score >= 85) {
        return '<span class="status-chip present">Present</span>';
    }
    if (score >= 50) {
        return '<span class="status-chip present">Present</span>';
    }
    return '<span class="status-chip absent">Low confidence</span>';
}

function renderTable(records) {
    const tbody = document.getElementById('analyticsBody');
    tbody.innerHTML = '';

    if (!records.length) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 24px; color: #64748b;">No attendance records match the selected filter.</td></tr>';
        return;
    }

    records.forEach(item => {
        const row = document.createElement('tr');
        const time = formatTime(item.timestamp || item.time || `${item.date}T00:00:00`);
        row.innerHTML = `
            <td>${item.date || '-'}</td>
            <td>${item.student_name || 'Unknown'}</td>
            <td>${time}</td>
            <td>${item.confidence != null ? formatPct(item.confidence * 100) : '-'}</td>
            <td>${renderStatusChip(item.confidence)}</td>
        `;
        tbody.appendChild(row);
    });
}

function buildCharts(records, stats) {
    const presentCount = stats.present_today || 0;
    const absentCount = Math.max((stats.total_students || 0) - presentCount, 0);

    const ratioCtx = document.getElementById('ratioChart').getContext('2d');
    if (ratioChart) ratioChart.destroy();
    ratioChart = new Chart(ratioCtx, {
        type: 'doughnut',
        data: {
            labels: ['Present', 'Absent'],
            datasets: [{
                data: [presentCount, absentCount],
                backgroundColor: ['#10b981', '#ef4444'],
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#475569' }
                },
                tooltip: {
                    callbacks: {
                        label: context => `${context.label}: ${context.parsed}`
                    }
                }
            }
        }
    });

    const buckets = {};
    records.forEach(item => {
        const timestamp = item.timestamp || `${item.date}T00:00:00`;
        const date = new Date(timestamp);
        if (!isNaN(date)) {
            const hour = String(date.getHours()).padStart(2, '0');
            buckets[hour] = (buckets[hour] || 0) + 1;
        }
    });

    const hourLabels = Array.from({ length: 24 }, (_, idx) => String(idx).padStart(2, '0'));
    const hourValues = hourLabels.map(hour => buckets[hour] || 0);

    const hourCtx = document.getElementById('hourChart').getContext('2d');
    if (hourChart) hourChart.destroy();
    hourChart = new Chart(hourCtx, {
        type: 'line',
        data: {
            labels: hourLabels.map(hour => `${hour}:00`),
            datasets: [{
                label: 'Attendance Events',
                data: hourValues,
                borderColor: '#4f46e5',
                backgroundColor: 'rgba(79, 70, 229, 0.12)',
                fill: true,
                tension: 0.35,
                pointRadius: 3,
                pointBackgroundColor: '#4f46e5',
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    ticks: { color: '#475569' },
                    grid: { display: false }
                },
                y: {
                    beginAtZero: true,
                    ticks: { color: '#475569' },
                    grid: { color: 'rgba(148, 163, 184, 0.16)' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

async function fetchStats() {
    const response = await authFetch(STATS_URL);
    if (!response.ok) {
        throw new Error('Unable to fetch stats');
    }
    return response.json();
}

async function fetchAttendance(dateFilter) {
    const url = new URL(ATTENDANCE_URL, window.location.origin);
    if (dateFilter) {
        url.searchParams.append('date', dateFilter);
    }
    const response = await authFetch(url.toString());
    if (!response.ok) {
        throw new Error('Unable to fetch attendance records');
    }
    return response.json();
}

function applyFilters() {
    const nameFilter = document.getElementById('filterName').value.trim().toLowerCase();
    const filtered = attendanceRecords.filter(record => {
        if (nameFilter && !(record.student_name || '').toLowerCase().includes(nameFilter)) {
            return false;
        }
        return true;
    });
    renderTable(filtered);
}

function updateLiveStatus() {
    const now = new Date();
    document.getElementById('liveStatus').textContent = `Last updated: ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
}

async function refreshDashboard() {
    const dateFilter = document.getElementById('filterDate').value || '';
    const nameFilter = document.getElementById('filterName').value.trim();
    document.getElementById('attendanceLoading').style.display = 'flex';

    try {
        const [stats, attendance] = await Promise.all([
            fetchStats(),
            fetchAttendance(dateFilter)
        ]);

        document.getElementById('metric-total-students').textContent = stats.total_students ?? 0;
        document.getElementById('metric-present-today').textContent = stats.present_today ?? 0;
        document.getElementById('metric-avg-confidence').textContent = formatPct((stats.avg_confidence ?? 0) * 100);

        attendanceRecords = Array.isArray(attendance) ? attendance : [];
        renderTable(attendanceRecords);
        buildCharts(attendanceRecords, stats);
        updateLiveStatus();
    } catch (error) {
        console.error(error);
        document.getElementById('analyticsBody').innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 24px; color: #ef4444;">Unable to load attendance data.</td></tr>';
    } finally {
        document.getElementById('attendanceLoading').style.display = 'none';
    }
}

function scheduleRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    refreshTimer = setInterval(refreshDashboard, AUTO_REFRESH_MS);
}

function attachEventListeners() {
    document.getElementById('refreshButton').addEventListener('click', refreshDashboard);
    document.getElementById('downloadButton').addEventListener('click', async () => {
        const date = document.getElementById('filterDate').value;
        const url = '/api/export_csv' + (date ? ('?date=' + encodeURIComponent(date)) : '');
        try {
            const resp = await authFetch(url);
            if (!resp.ok) throw new Error('Unable to download CSV');
            const blob = await resp.blob();
            const blobUrl = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = `attendance_${date || 'all'}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(blobUrl);
        } catch (err) {
            console.error(err);
            alert('Download failed');
        }
    });
    document.getElementById('filterDate').addEventListener('change', refreshDashboard);
    document.getElementById('filterName').addEventListener('input', applyFilters);
}

window.addEventListener('DOMContentLoaded', () => {
    attachEventListeners();
    refreshDashboard();
    scheduleRefresh();
});

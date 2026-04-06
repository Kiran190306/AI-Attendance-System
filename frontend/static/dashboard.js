// fetch stats and populate dashboard
async function loadStats() {
    const resp = await fetch('/api/attendance/today');
    const stats = await resp.json();
    document.getElementById('total-students').textContent = stats.total_students;
    document.getElementById('present-today').textContent = stats.present_today;
    document.getElementById('late-students').textContent = stats.late_students;
    // build simple chart: present vs absent
    const ctx = document.getElementById('attendanceChart').getContext('2d');
    const absent = stats.total_students - stats.present_today;
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Present','Absent'],
            datasets: [{
                data: [stats.present_today, absent],
                backgroundColor: ['#4caf50','#f44336']
            }]
        },
        options: {
            responsive: true
        }
    });
}

window.addEventListener('load', loadStats);

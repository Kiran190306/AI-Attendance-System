// Access camera and draw to hidden canvas when capture button clicked
const video = document.getElementById('video');
const captureBtn = document.getElementById('captureBtn');

navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(err => {
        console.error('camera error', err);
        document.getElementById('result').textContent = 'Camera access denied';
    });

captureBtn.addEventListener('click', async () => {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
    // send to API
    const deviceId = localStorage.getItem('device_id') || '';
    const deviceToken = localStorage.getItem('device_token') || '';
    const resp = await sendAttendance(dataUrl, deviceId, deviceToken);
    document.getElementById('result').textContent = JSON.stringify(resp);
});

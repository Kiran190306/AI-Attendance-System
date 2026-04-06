// handles communication with backend mobile API
async function sendAttendance(imageData, deviceId, deviceToken) {
    try {
        const resp = await fetch('/api/mobile/attendance', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                image_data: imageData,
                device_id: deviceId,
                device_token: deviceToken
            })
        });
        return await resp.json();
    } catch (e) {
        console.error('mobile api error', e);
        return {error: 'network'};
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // API Key Handling
    const apiKeyInput = document.getElementById('api-key');
    const savedKey = localStorage.getItem('google_maps_api_key');
    if (savedKey) {
        apiKeyInput.value = savedKey;
    }

    apiKeyInput.addEventListener('change', (e) => {
        localStorage.setItem('google_maps_api_key', e.target.value);
    });

    // Tab Switching
    const tabs = document.querySelectorAll('.tab-btn');
    const contents = document.querySelectorAll('.tab-content');

    // Instructions Data
    const instructions = {
        'optimize-trip': `
            <p>1. Enter your origin and destination</p>
            <p>2. Select your target Departure Window</p>
            <p>3. Click "Find Best Time" to see the fastest options within this window</p>`,
        'optimize-work': `
            <p>1. Enter Starting Address(es) and a Destination (like a workplace)</p>
            <p>2. Set how long you need to be at the destination (Hours)</p>
            <p>3. Select the earliest time you can depart from your starting address(es) for the departure window start and the latest time you can depart from your starting address(es) for the departure window end</p>
            <p>4. Click "Find Best Schedule" to minimize total round-trip time</p>`
    };

    const stepsContainer = document.getElementById('steps-text');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            const tabId = tab.dataset.tab;
            document.getElementById(tabId).classList.add('active');

            // Update instructions
            if (instructions[tabId]) {
                stepsContainer.innerHTML = instructions[tabId];
            }

            // Clear results when switching tabs
            document.getElementById('results-area').classList.add('hidden');
        });
    });

    // Forms Handling
    setupForm('form-optimize-trip', '/api/optimize-trip', renderOptimizeTripResults);
    setupForm('form-optimize-work', '/api/optimize-work', renderOptimizeWorkResults);

    // Pre-fill date and time inputs
    const now = new Date();
    // Helper to get local date strings
    const pad = (n) => n < 10 ? '0' + n : n;
    const dateStr = now.getFullYear() + '-' + pad(now.getMonth() + 1) + '-' + pad(now.getDate());
    const timeStr = pad(now.getHours()) + ':' + pad(now.getMinutes());

    document.querySelectorAll('input[type="date"]').forEach(input => input.value = dateStr);
    document.querySelectorAll('input[type="time"]').forEach(input => input.value = timeStr);
});

function setupForm(formId, endpoint, renderCallback) {
    const form = document.getElementById(formId);
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const apiKey = document.getElementById('api-key').value;
        if (!apiKey) {
            alert("Please enter a Google Maps API Key first.");
            return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.textContent;
        submitBtn.textContent = "Processing...";
        submitBtn.disabled = true;

        const formData = new FormData(form);
        const rawData = Object.fromEntries(formData.entries());
        const data = {};

        // Manual construction of result data
        data.api_key = apiKey;
        data.destination = rawData.destination;

        // Handle textarea for origins (works for both Compare and Optimize Work now)
        if (rawData.origins) {
            data.origins = rawData.origins.split('\n').map(s => s.trim()).filter(s => s);
        }
        // Fallback for single origin input if used in other forms (Optimize Trip)
        if (rawData.origin) {
            data.origin = rawData.origin;
        }
        if (rawData.work_duration_hours) {
            data.work_duration_hours = rawData.work_duration_hours;
        }

        // Helper to combine date+time
        const combine = (dateKey, timeKey) => {
            if (rawData[dateKey] && rawData[timeKey]) {
                // Ensure seconds are added for ISO format
                return `${rawData[dateKey]}T${rawData[timeKey]}:00`;
            }
            return null;
        };

        if (rawData.window_start_date) data.window_start = combine('window_start_date', 'window_start_time');
        if (rawData.window_end_date) data.window_end = combine('window_end_date', 'window_end_time');
        if (rawData.departure_date) data.departure_time = combine('departure_date', 'departure_time');

        // Debug logging
        console.log('Sending data:', data);

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                const resultsArea = document.getElementById('results-area');
                const resultsContent = document.getElementById('results-content');
                resultsArea.classList.remove('hidden');
                renderCallback(result, resultsContent);
            } else {
                alert(`Error: ${result.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Submit error:', error);
            alert(`Network or Server Error. Check console for details.\n\nMessage: ${error.message}`);
        } finally {
            submitBtn.textContent = originalBtnText;
            submitBtn.disabled = false;
        }
    });
}

function formatTime(isoString) {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });
}

function renderOptimizeTripResults(data, container) {
    if (!data.results || data.results.length === 0) {
        container.innerHTML = "<p>No routes found within this window.</p>";
        return;
    }

    let html = '';
    if (data.best_departure) {
        html += `
            <div class="result-item best-result">
                <h4>⭐ Shortest Travel Time</h4>
                <div class="prop"><span class="prop-label">Departure</span><span class="prop-value">${formatTime(data.best_departure)}</span></div>
                <div class="prop"><span class="prop-label">Arrival</span><span class="prop-value">${data.results.find(r => r.departure_time === data.best_departure)?.arrival_text || 'N/A'}</span></div>
                <div class="prop"><span class="prop-label">Duration</span><span class="prop-value">${Math.round(data.min_duration_seconds / 60)} mins</span></div>
                <div class="prop"><span class="prop-label">Route</span><span class="prop-value">${data.best_route_summary || 'N/A'}</span></div>
            </div>
            <h4>All Options Checked:</h4>
        `;
    }

    data.results.forEach(item => {
        html += `
            <div class="result-item">
                <div class="prop"><span class="prop-label">Departure</span><span class="prop-value">${formatTime(item.departure_time)}</span></div>
                <div class="prop"><span class="prop-label">Arrival</span><span class="prop-value">${item.arrival_text || 'N/A'}</span></div>
                <div class="prop"><span class="prop-label">Duration</span><span class="prop-value">${item.duration_text}</span></div>
                <div class="prop"><span class="prop-label">Route</span><span class="prop-value">${item.route_summary || 'N/A'}</span></div>
            </div>
        `;
    });

    container.innerHTML = html;
}


function renderOptimizeWorkResults(data, container) {
    if (!data.results || data.results.length === 0) {
        container.innerHTML = "<p>No viable schedules found.</p>";
        return;
    }

    let html = '';
    if (data.best_schedule) {
        const bs = data.best_schedule;
        html += `
            <div class="result-item best-result">
                <h4>⭐ Shortest Commute (Total: ${bs.total_commute_text})</h4>
                <div class="prop"><span class="prop-label">Origin</span><span class="prop-value">${bs.origin}</span></div>
                <div class="prop"><span class="prop-label">Leave Home</span><span class="prop-value">${formatTime(bs.departure_to_work)}</span></div>
                <div class="prop"><span class="prop-label">Arrive Work</span><span class="prop-value">~${Math.round(bs.duration_to_work / 60)} mins (${bs.route_to_work})</span></div>
                <div class="prop"><span class="prop-label">Leave Work</span><span class="prop-value">${formatTime(bs.leave_work_time)}</span></div>
                <div class="prop"><span class="prop-label">Arrive Home</span><span class="prop-value">~${Math.round(bs.duration_to_home / 60)} mins (${bs.route_to_home})</span></div>
            </div>
            <h4>All Options (Sorted by Time):</h4>
        `;
    }

    data.results.forEach(item => {
        html += `
            <div class="result-item">
                <div class="prop"><span class="prop-label">Origin</span><span class="prop-value">${item.origin}</span></div>
                <div class="prop"><span class="prop-label">Schedule</span><span class="prop-value">${formatTime(item.departure_to_work)} ➝ ${formatTime(item.leave_work_time)}</span></div>
                <div class="prop"><span class="prop-label">Total Commute</span><span class="prop-value">${item.total_commute_text}</span></div>
            </div>
        `;
    });

    container.innerHTML = html;
}

async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        
        document.getElementById('server-count').innerText = data.parsed_urls.length;
        document.getElementById('status-message').innerText = data.scan_state.status_message;
        document.getElementById('accounts-found').innerText = data.scan_state.found_accounts;
        document.getElementById('current-url').innerText = data.scan_state.current_url ? `Target: ${data.scan_state.current_url}` : 'Target: None';

        if (data.scan_state.total > 0) {
            const pct = Math.round((data.scan_state.progress / data.scan_state.total) * 100);
            document.getElementById('progress-fill').style.width = `${pct}%`;
            document.getElementById('progress-percent').innerText = `${pct}%`;
        } else {
            document.getElementById('progress-fill').style.width = '0%';
            document.getElementById('progress-percent').innerText = '0%';
        }

        renderServers(data.parsed_urls);
    } catch (err) {
        console.error("Failed to fetch status", err);
    }
}

function renderServers(urls) {
    const list = document.getElementById('server-list');
    if (!urls || urls.length === 0) {
        list.innerHTML = '<li class="empty">No servers loaded. Click "Search Servers" to begin.</li>';
        return;
    }
    
    list.innerHTML = urls.map((url, idx) => `
        <li>
            <span>[${idx}] ${url}</span>
            <button class="btn btn-secondary" onclick="scanSpecific('${url}')">Scan</button>
        </li>
    `).join('');
}

async function searchLinks() {
    document.getElementById('status-message').innerText = "Fetching links...";
    await fetch('/api/search-links', { method: 'POST' });
}

async function changeLanguage() {
    const lang = document.getElementById('lang-select').value;
    await fetch('/api/change-language', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: lang })
    });
}

async function startScan(url = null) {
    await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
    });
}

function scanSpecific(url) {
    startScan(url);
}

async function loadOutputs() {
    try {
        const res = await fetch('/api/outputs');
        const data = await res.json();
        const list = document.getElementById('playlist-list');
        
        if (!data.files || data.files.length === 0) {
            list.innerHTML = '<li class="empty">No playlists generated yet.</li>';
            return;
        }

        list.innerHTML = data.files.map(file => `
            <li>
                <span>📁 ${file.path}</span>
                <a href="/api/download/${file.path}" class="btn btn-primary" download>Download</a>
            </li>
        `).join('');
    } catch (err) {
        console.error("Failed to load outputs", err);
    }
}

// Poll status every 2 seconds
setInterval(fetchStatus, 2000);
fetchStatus();
loadOutputs();

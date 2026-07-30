function formatSeconds(seconds) {
    if (!seconds || seconds <= 0) return "--:--";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs < 10 ? '0' : ''}${secs}s remaining`;
}

async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        
        document.getElementById('server-count').innerText = data.parsed_urls.length;
        document.getElementById('status-message').innerText = data.scan_state.status_message;
        document.getElementById('accounts-found').innerText = data.scan_state.found_accounts;
        document.getElementById('current-url').innerText = data.scan_state.current_url ? `Target: ${data.scan_state.current_url}` : 'Target: None';

        const isScanning = data.scan_state.is_scanning;
        document.getElementById('btn-cancel-scan').style.display = isScanning ? 'inline-block' : 'none';
        document.getElementById('btn-attack-all').style.display = isScanning ? 'none' : 'inline-block';

        if (data.scan_state.total > 0) {
            const pct = Math.round((data.scan_state.progress / data.scan_state.total) * 100);
            document.getElementById('progress-fill').style.width = `${pct}%`;
            document.getElementById('progress-percent').innerText = `${pct}%`;

            if (isScanning && data.scan_state.eta_seconds > 0) {
                document.getElementById('eta-time').innerText = `ETA: ${formatSeconds(data.scan_state.eta_seconds)}`;
            } else if (isScanning) {
                document.getElementById('eta-time').innerText = `ETA: Calculating...`;
            } else {
                document.getElementById('eta-time').innerText = `ETA: 00m 00s`;
            }
        } else {
            document.getElementById('progress-fill').style.width = '0%';
            document.getElementById('progress-percent').innerText = '0%';
            document.getElementById('eta-time').innerText = 'ETA: --:--';
        }

        renderServers(data.parsed_urls);
        renderTerminalLogs(data.scan_state.logs);
        renderAccountsTable(data.found_accounts_list);
        loadOutputs();
    } catch (err) {
        console.error("Failed to fetch status", err);
    }
}

function renderServers(urls) {
    const list = document.getElementById('server-list');
    if (!urls || urls.length === 0) {
        list.innerHTML = '<li class="empty">No servers loaded. Click "Auto-Search Web", paste multiple URLs, or upload a .txt file.</li>';
        return;
    }
    
    list.innerHTML = urls.map((url, idx) => `
        <li>
            <span>[${idx}] ${url}</span>
            <div>
                <button class="btn btn-secondary btn-sm" onclick="removeServer('${url}')">❌</button>
                <button class="btn btn-accent btn-sm" onclick="scanSpecific('${url}')">Attack</button>
            </div>
        </li>
    `).join('');
}

async function removeServer(url) {
    try {
        await fetch('/api/remove-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        fetchStatus();
    } catch (err) {
        console.error("Failed to remove server", err);
    }
}

async function saveServers() {
    try {
        const res = await fetch('/api/save-servers', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
    } catch (err) {
        console.error("Failed to save servers", err);
    }
}

async function clearServers() {
    if (!confirm("Are you sure you want to clear all target servers from the list?")) return;
    try {
        const res = await fetch('/api/clear-servers', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            fetchStatus();
        }
    } catch (err) {
        console.error("Failed to clear servers", err);
    }
}

async function uploadServerFile(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/upload-server-list', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            alert(`File uploaded! Added ${data.added_count} new server(s).`);
            fetchStatus();
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (err) {
        console.error("Failed to upload server list file", err);
    }
}

function renderAccountsTable(accounts) {
    const tbody = document.getElementById('accounts-table-body');
    if (!accounts || accounts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty">No accounts found yet. Run scan to discover credentials.</td></tr>';
        return;
    }

    tbody.innerHTML = accounts.map(acc => `
        <tr>
            <td><code>${acc.server}</code></td>
            <td><strong class="text-user">${acc.username}</strong></td>
            <td><strong class="text-pass">${acc.password}</strong></td>
            <td>
                <a href="/api/download/${acc.file_path}" class="btn btn-accent btn-sm" download>📥 Download</a>
                <button class="btn btn-danger btn-sm" onclick="deleteOutput('${acc.file_path}')">🗑️ Delete</button>
            </td>
        </tr>
    `).join('');
}

function renderTerminalLogs(logs) {
    const container = document.getElementById('terminal-output');
    if (!logs || logs.length === 0) {
        container.innerHTML = '<div class="log-line">IPTV Console Ready...</div>';
        return;
    }

    const html = logs.map(line => {
        if (line.includes("ACCOUNT FOUND") || line.includes("SUCCESS!")) {
            return `<div class="log-line log-found">🔥 ${line}</div>`;
        }
        return `<div class="log-line">${line}</div>`;
    }).join('');

    container.innerHTML = html;
    container.scrollTop = container.scrollHeight;
}

async function searchLinks() {
    const limit = document.getElementById('search-limit-select').value;
    document.getElementById('status-message').innerText = `Searching web for up to ${limit} IPTV servers...`;
    try {
        await fetch('/api/search-links', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limit: limit })
        });
        setTimeout(fetchStatus, 500);
    } catch (err) {
        console.error("Failed to start search", err);
    }
}

async function addCustomUrl() {
    const input = document.getElementById('custom-url-input');
    const url = input.value.trim();
    if (!url) return;
    
    try {
        const res = await fetch('/api/add-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        const data = await res.json();
        if (res.ok) {
            input.value = '';
            alert(data.message);
            fetchStatus();
        } else {
            alert(data.message || 'Invalid or duplicate server URL.');
        }
    } catch (err) {
        console.error("Failed to add URL", err);
    }
}

async function testManualCredentials() {
    const serverInput = document.getElementById('manual-server');
    const userInput = document.getElementById('manual-user');
    const passInput = document.getElementById('manual-pass');

    const server = serverInput.value.trim();
    const username = userInput.value.trim();
    const password = passInput.value.trim();

    if (!server || !username || !password) {
        alert("Please enter Server URL, Username, and Password.");
        return;
    }

    document.getElementById('status-message').innerText = `Testing ${username}:${password} on ${server}...`;
    try {
        const res = await fetch('/api/test-credentials', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ server: server, username: username, password: password })
        });
        const data = await res.json();
        alert(data.message);
        fetchStatus();
    } catch (err) {
        alert("Error testing credentials: " + err);
        console.error("Failed to test credentials", err);
    }
}

async function startScan(url = null) {
    const attackMode = document.getElementById('attack-mode-select').value;
    const threads = document.getElementById('threads-select').value;
    await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url, mode: attackMode, threads: threads })
    });
}

async function attackAllServers() {
    const attackMode = document.getElementById('attack-mode-select').value;
    const threads = document.getElementById('threads-select').value;
    await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ attack_all: true, mode: attackMode, threads: threads })
    });
}

async function cancelScan() {
    await fetch('/api/cancel-scan', { method: 'POST' });
}

function scanSpecific(url) {
    startScan(url);
}

async function deleteOutput(filepath) {
    if (!confirm(`Are you sure you want to delete ${filepath}?`)) return;
    try {
        const res = await fetch(`/api/delete-output/${filepath}`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            fetchStatus();
            loadOutputs();
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (err) {
        console.error("Failed to delete output file", err);
    }
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
                <div>
                    <a href="/api/download/${file.path}" class="btn btn-primary btn-sm" download>Download</a>
                    <button class="btn btn-danger btn-sm" onclick="deleteOutput('${file.path}')">🗑️ Delete</button>
                </div>
            </li>
        `).join('');
    } catch (err) {
        console.error("Failed to load outputs", err);
    }
}

setInterval(fetchStatus, 1500);
fetchStatus();
loadOutputs();

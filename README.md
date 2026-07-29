# IPTV Web & CLI Dashboard

## Disclaimer

This program is just a demonstration. **It's not intended** for personal purpose.

## What is this?

IPTV is a Python 3 web & CLI application that lets you crawl search engines to analyze IPTV servers.

---

## 🌐 Web Interface (Recommended)

IPTV features a modern, responsive web dashboard allowing you to search servers, trigger brute-force tasks, view live scan progress, and download generated `.m3u` playlists directly from your browser.

### 🚀 Quick Start with Docker Compose

1. Clone or download `docker-compose.yml`:
   ```yaml
   version: '3.8'

   services:
     iptv-web:
       image: ghcr.io/jsanderstechnologies/iptv:latest
       container_name: iptv-web
       ports:
         - "5000:5000"
       restart: unless-stopped
       environment:
         - PYTHONUNBUFFERED=1
       volumes:
         - ./output:/app/iptv/output
   ```

2. Start the web service:
   ```bash
   docker compose up -d
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

---

### 🐳 Running with Docker CLI

**Run Web Interface Container:**
```bash
docker run -d -p 5000:5000 -v $(pwd)/output:/app/iptv/output --name iptv-web ghcr.io/jsanderstechnologies/iptv:latest
```

**Run Interactive CLI Version in Container:**
```bash
docker run -it --rm -v $(pwd)/output:/app/iptv/output ghcr.io/jsanderstechnologies/iptv:latest python iptv.py
```

---

## 💻 Running Locally (Without Docker)

1. Clone the repository:
   ```bash
   git clone https://github.com/jsanderstechnologies/IPTV.git
   cd IPTV/iptv
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch Web Application:
   ```bash
   python app.py
   ```
   *(Access via `http://localhost:5000`)*

4. Or Launch CLI Application:
   ```bash
   python iptv.py
   ```

---

## 📜 License

See [the license](LICENSE) for further details.

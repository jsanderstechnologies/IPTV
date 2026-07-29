import os
import random
import threading
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import Crawler

app = Flask(__name__)
CORS(app)

crawler = Crawler.Crawler("it")

scan_state = {
    "is_scanning": False,
    "progress": 0,
    "total": 0,
    "current_url": "",
    "status_message": "Idle",
    "found_accounts": 0
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({
        "version": crawler.version,
        "language": crawler.language,
        "parsed_urls": crawler.parsedUrls,
        "scan_state": scan_state
    })

@app.route("/api/search-links", methods=["POST"])
def search_links():
    def do_search():
        scan_state["status_message"] = "Fetching IPTV links from search engines..."
        crawler.search_links()
        scan_state["status_message"] = f"Found {len(crawler.parsedUrls)} server URLs"

    thread = threading.Thread(target=do_search)
    thread.start()
    return jsonify({"status": "Search started", "parsed_urls_count": len(crawler.parsedUrls)})

@app.route("/api/change-language", methods=["POST"])
def change_language():
    data = request.json or {}
    lang = data.get("language", "it")
    success = crawler.change_language(lang)
    if success:
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
        
        target_url = url if url else (random.choice(crawler.parsedUrls) if crawler.parsedUrls else None)
        if not target_url:
            scan_state["is_scanning"] = False
            scan_state["status_message"] = "No server URLs available. Run search first."
            return

        scan_state["current_url"] = target_url
        scan_state["status_message"] = f"Scanning {target_url}..."

        lang_file = os.path.join(crawler.languageDir, crawler.language + ".txt")
        if not os.path.exists(lang_file):
            scan_state["is_scanning"] = False
            scan_state["status_message"] = "Language file missing."
            return

        with open(lang_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f if line.strip()]

        scan_state["total"] = len(lines)
        found = 0

        headers = {'User-Agent': 'Mozilla/5.0'}
        import requests
        for idx, username in enumerate(lines, start=1):
            scan_state["progress"] = idx
            target = target_url + crawler.basicString % (username, username)
            try:
                res = requests.get(target, headers=headers, timeout=4)
                if res.status_code == 200 and len(res.text) > 0 and "#EXTM3U" in res.text:
                    domain = target_url.replace("http://", "").replace("https://", "").strip("/")
                    new_path = os.path.join(crawler.outputDir, domain)
                    crawler.create_file(username, new_path, res.text)
                    found += 1
                    scan_state["found_accounts"] = found
            except Exception:
                pass

        if target_url in crawler.parsedUrls:
            crawler.parsedUrls.remove(target_url)

        scan_state["is_scanning"] = False
        scan_state["status_message"] = f"Scan complete for {target_url}. Found {found} accounts."

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

app.run(host="0.0.0.0", port=5000)

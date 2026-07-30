#!/usr/bin/env python3
import sys
import Crawler
import warnings
from clint.textui import colored

# Global Variables
warnings.filterwarnings("ignore")
cr = Crawler.Crawler("en")

"""Print menu
Easy menu for CLI navigation
"""
def menu():
    print("")
    print(colored.yellow("################"))
    print(colored.yellow("##### IPTV #####"))
    print(colored.yellow("##### v" + cr.version + " ###"))
    print(colored.yellow("################"))
    print("")
    print(colored.blue("Menu"))
    print("0 - Exit")
    print("1 - Search for IPTV Servers")
    print("2 - Look at the servers list")
    print("3 - Brute force all servers from the list")
    print("4 - Brute force random server from the list")
    print("5 - Brute force specific server from the list")
    print("6 - Manually add custom server URL to list")
    print("")

def safe_input(prompt=""):
    try:
        return input(prompt)
    except EOFError:
        print("\n" + colored.red("EOF received or non-interactive terminal stream. Exiting..."))
        sys.exit(0)

while True:
    menu()
    try:
        raw_val = safe_input("Please select an option: ")
        if not raw_val:
            continue
        choosenMenu = int(raw_val)
    except ValueError:
        print(colored.red("Please enter a valid number"))
        continue

    if choosenMenu == 0:
        print(colored.red("Bye bye"))
        break
    elif choosenMenu == 1:
        print(colored.green("Fetching URLs please wait..."))
        found = cr.search_links()
        print(colored.green(f"Done, {found} new URLs found. Total: {len(cr.parsedUrls)}"))
    elif choosenMenu == 2:
        print(colored.green("Printing server list"))
        if not cr.parsedUrls:
            print(colored.red("No servers found or added yet."))
        for index, server in enumerate(cr.parsedUrls):
            print(f"[{index}] - {server}")
    elif choosenMenu == 3:
        for i in range(len(cr.parsedUrls)):
            url = cr.parsedUrls[i]
            print(colored.green(f"Attacking {url}..."))
    elif choosenMenu == 4:
        if cr.parsedUrls:
            import random
            url = random.choice(cr.parsedUrls)
            print(colored.green(f"Attacking random server {url}..."))
        else:
            print(colored.red("No servers in list."))
    elif choosenMenu == 5:
        try:
            index = int(safe_input("Please provide the number near the URLs found: "))
            url = cr.parsedUrls[index]
            print(colored.green(f"Attacking {url}..."))
        except IndexError:
            print(colored.red(f"No URL found at index: {index}"))
        except ValueError:
            print(colored.red("You have entered a wrong value, please provide a NUMBER. Use option 2 first"))
    elif choosenMenu == 6:
        custom_url = safe_input("Please enter custom server URL (e.g. http://domain.com:8080): ").strip()
        if cr.add_custom_url(custom_url):
            print(colored.green(f"Successfully added server: {custom_url}"))
        else:
            print(colored.red("Invalid or duplicate URL entered."))
    else:
        print(colored.red("Option not recognized"))

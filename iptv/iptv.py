#!/usr/bin/env python3
import sys
import Crawler
import warnings
from clint.textui import colored

# Global Variables
warnings.filterwarnings("ignore")
cr = Crawler.Crawler("it")

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
    print("1 - Search for some Servers")
    print("2 - Look at the servers list")
    print("3 - Select language, default is Italian")
    print("4 - Brute force all server from the list")
    print("5 - Brute force random server from the list")
    print("6 - Brute force specific server from the list")
    print("7 - Manually add custom server URL to list")
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
        cr.search_links()
        print(colored.green(f"Done, {len(cr.parsedUrls)} URLs found"))
    elif choosenMenu == 2:
        print(colored.green("Printing server list"))
        if not cr.parsedUrls:
            print(colored.red("No servers found or added yet."))
        for index, server in enumerate(cr.parsedUrls):
            print(f"[{index}] - {server}")
    elif choosenMenu == 3:
        language = str(safe_input("What language do you need? (it, en, es): "))
        if cr.change_language(language):
            print(colored.green(f"Language changed, the system now will attack the servers with {language}.txt"))
        else:
            print(colored.red(f"Language not changed, the file language for {language} does not exist"))
    elif choosenMenu == 4:
        for i in range(len(cr.parsedUrls)):
            url = cr.parsedUrls[i]
            result = cr.search_accounts(url)
            print(colored.green(result))
    elif choosenMenu == 5:
        result = cr.search_accounts()
        print(colored.green(result))
    elif choosenMenu == 6:
        try:
            index = int(safe_input("Please provide the number near the URLs found: "))
            url = cr.parsedUrls[index]
            result = cr.search_accounts(url)
            print(colored.green(result))
        except IndexError:
            print(colored.red(f"No URL found at index: {index}"))
        except ValueError:
            print(colored.red("You have entered a wrong value, please provide a NUMBER. Use option 2 first"))
    elif choosenMenu == 7:
        custom_url = safe_input("Please enter custom server URL (e.g. http://domain.com:8080): ").strip()
        if cr.add_custom_url(custom_url):
            print(colored.green(f"Successfully added server: {custom_url}"))
        else:
            print(colored.red("Invalid or duplicate URL entered."))
    else:
        print(colored.red("Option not recognized"))

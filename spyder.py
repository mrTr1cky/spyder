#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
  ____                  _      ____                  
 / ___|___  _ __  _   _| |_   / ___|  ___ __ _ _ __  
| |   / _ \| '_ \| | | | __| | |  _ / __/ _` | '_ \ 
| |__| (_) | | | | |_| | |_  | |_| | (_| (_| | | | |
 \____\___/|_| |_|\__,_|\__|  \____|\___\__,_|_| |_|

Spyder - Domain Scanner

Author: madtiger
Telegram: @DevidLuce
Address: [Uganda]

"""

import sys
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import argparse
from urllib.parse import urljoin, urlparse
from colorama import init, Fore, Style

# Initialize colorama for cross-platform support
init(autoreset=True)

# Set of discovered URLs
discovered_urls = set()

# Helper function to fetch URLs
def fetch_url(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response
        else:
            print(f"{Fore.RED}[!] Failed to fetch URL: {url}{Style.RESET_ALL}")
            return None
    except requests.RequestException as e:
        print(f"{Fore.RED}[!] Error fetching URL: {url} - {e}{Style.RESET_ALL}")
        return None

# Function to extract directories, parameters, endpoints from response
def extract_info(response, base_url):
    soup = BeautifulSoup(response.text, 'html.parser')
    links = set()
    
    # Extract links from <a> tags
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        full_url = urljoin(base_url, href)
        links.add(full_url)

    # Extract links from <script> tags
    for script in soup.find_all('script', src=True):
        src = script.get('src')
        full_url = urljoin(base_url, src)
        links.add(full_url)

    # Extract links from <link> tags
    for link in soup.find_all('link', href=True):
        href = link.get('href')
        full_url = urljoin(base_url, href)
        links.add(full_url)

    # Extract links from JSON, CSS
    for link in soup.find_all(['script', 'link']):
        if link.has_attr('src'):
            src = link.get('src')
            full_url = urljoin(base_url, src)
            links.add(full_url)
        elif link.has_attr('href'):
            href = link.get('href')
            full_url = urljoin(base_url, href)
            links.add(full_url)

    return links

# Function to recursively scan directories
def recursive_scan(base_url, depth=0, max_depth=3):
    if depth > max_depth:
        return

    if base_url in discovered_urls:
        return

    response = fetch_url(base_url)
    if response is not None:
        discovered_urls.add(base_url)
        print(f"{Fore.GREEN}[+] Discovered URL: {base_url}{Style.RESET_ALL}")

        links = extract_info(response, base_url)
        for link in links:
            if urlparse(link).netloc == urlparse(base_url).netloc:
                recursive_scan(link, depth + 1)

# Function to check validity of URLs from dir.txt
def check_dir_txt(base_url, dir_file):
    with open(dir_file, 'r', encoding='utf-8') as file:
        for line in file:
            dir_url = urljoin(base_url, line.strip())
            if fetch_url(dir_url):
                print(f"{Fore.YELLOW}[*] Valid dir from dir.txt: {dir_url}{Style.RESET_ALL}")

# Main function
def main():
    parser = argparse.ArgumentParser(description="Domain Scanner")
    parser.add_argument('-d', '--domain', help='Single domain to scan')
    parser.add_argument('-l', '--list', help='File containing list of domains to scan')
    parser.add_argument('-f', '--file', help='Directory file to check for valid URLs (default: dir.txt)', default='dir.txt')
    parser.add_argument('-t', '--threads', type=int, default=10, help='Number of threads (default: 10)')
    args = parser.parse_args()

    domains = []
    if args.domain:
        domains.append(args.domain)
    if args.list:
        with open(args.list, 'r', encoding='utf-8') as file:
            domains.extend(file.read().splitlines())

    if not domains:
        # Read domains from stdin (for use with subfinder or similar tools)
        for line in sys.stdin:
            domains.append(line.strip())

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = []
        for domain in domains:
            futures.append(executor.submit(recursive_scan, domain))
            futures.append(executor.submit(check_dir_txt, domain, args.file))
        
        # Wait for all futures to complete
        concurrent.futures.wait(futures)

    # Write discovered URLs to results.txt
    with open('results.txt', 'w', encoding='utf-8') as result_file:
        for url in discovered_urls:
            result_file.write(f"{url}\n")

if __name__ == "__main__":
    main()

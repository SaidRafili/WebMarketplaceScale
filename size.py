import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import math
import sys

START_INDEX = 12000     
END_INDEX = 14000    

INPUT_FILE = "azurl.txt"
OUTPUT_FILE = f"az_visitors_{START_INDEX}_{END_INDEX}.csv"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
POLITE_DELAY = (1.0, 1.8)

USE_SERP_API = False
SERP_PROVIDER = "serper"
SERP_API_KEY = "YOUR_SERP_API_KEY"

# Calibration constants
SIZE_KB_MULTIPLIER = 2.0
LINKS_MULTIPLIER = 0.8
VISITORS_SCALE = 10.0
MIN_VISITORS = 1
MAX_VISITORS = 50_000_000

# Helpers
def rand_sleep():
    time.sleep(random.uniform(*POLITE_DELAY))


def domain_is_alive(domain):
    for scheme in ("https://", "http://"):
        try:
            r = requests.head(scheme + domain, timeout=6, headers=HEADERS, allow_redirects=True)
            if r.status_code < 400:
                return True
        except requests.RequestException:
            pass
    return False


def fetch_homepage(domain):
    for scheme in ("https://", "http://"):
        try:
            r = requests.get(scheme + domain, timeout=12, headers=HEADERS)
            if r.status_code < 400 and r.text:
                html = r.text
                size_kb = len(html) / 1024.0
                soup = BeautifulSoup(html, "html.parser")
                return html, size_kb, soup
        except requests.RequestException:
            pass
    return None, 0.0, None


def count_internal_links(soup, domain):
    if soup is None:
        return 0
    domain_lower = domain.lower()
    count = 0
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if href.startswith("/") or domain_lower in href:
            count += 1
    return count

# Optional SERP API
def get_indexed_pages_serper(domain):
    if not SERP_API_KEY:
        return None
    try:
        url = "https://api.serper.dev/search"
        headers = {"X-API-KEY": SERP_API_KEY, "Content-Type": "application/json"}
        payload = {"q": f"site:{domain}"}
        r = requests.post(url, json=payload, headers=headers, timeout=12)
        if r.status_code != 200:
            return None
        data = r.json()
        import re
        text = str(data)
        m = re.search(r"About\s*([\d,]+)\s*results", text, re.IGNORECASE)
        if m:
            return int(m.group(1).replace(",", ""))
        org = data.get("organic", None)
        if isinstance(org, list):
            return max(1, len(org))
        return None
    except Exception:
        return None


def get_indexed_pages_via_serp(domain):
    if SERP_PROVIDER == "serper":
        return get_indexed_pages_serper(domain)
    return None

# Heuristics
def heuristic_indexed_pages(domain, size_kb, internal_links):
    base = 1.0
    size_effect = size_kb * SIZE_KB_MULTIPLIER
    link_effect = math.sqrt(internal_links + 1) * LINKS_MULTIPLIER
    pages_est = base + (size_effect * (1 + link_effect / 10.0))
    return int(max(1, round(pages_est)))


def combine_into_visitors(indexed_pages, size_kb, internal_links, alive):
    score = float(indexed_pages)
    score *= (1.0 + (size_kb / 100.0))
    score *= (1.0 + (math.log1p(internal_links) / 5.0))
    visitors = int(score * VISITORS_SCALE)
    if not alive:
        visitors = max(MIN_VISITORS, int(visitors * 0.05))
    visitors = int(visitors * random.uniform(0.9, 1.1))
    return max(MIN_VISITORS, min(MAX_VISITORS, visitors))

# Main processing
def process_domain(domain):
    alive = domain_is_alive(domain)
    html, size_kb, soup = fetch_homepage(domain)
    internal_links = count_internal_links(soup, domain)
    indexed = None
    if USE_SERP_API and SERP_API_KEY:
        indexed = get_indexed_pages_via_serp(domain)
    if indexed is None:
        indexed = heuristic_indexed_pages(domain, size_kb, internal_links)
    visitors_est = combine_into_visitors(indexed, size_kb, internal_links, alive)
    return {
        "domain": domain,
        "alive": alive,
        "homepage_kb": round(size_kb, 2),
        "internal_links": internal_links,
        "indexed_pages_est": indexed,
        "visitors_est_monthly": visitors_est
    }


def main():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            all_domains = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Input file '{INPUT_FILE}' not found.")
        sys.exit(1)

    # Slice based on range
    total = len(all_domains)
    start = max(0, START_INDEX)
    end = min(total, END_INDEX)
    domains = all_domains[start:end]
    print(f"Processing domains {start} to {end} (total: {len(domains)} of {total})\n")

    results = []
    for i, domain in enumerate(domains, start + 1):
        try:
            res = process_domain(domain)
        except Exception as e:
            print(f"{i:05}. {domain:30} → ERROR: {e}")
            res = {
                "domain": domain,
                "alive": False,
                "homepage_kb": 0.0,
                "internal_links": 0,
                "indexed_pages_est": 1,
                "visitors_est_monthly": MIN_VISITORS
            }
        results.append(res)
        print(f"{i:05}. {res['domain']:30} → {res['visitors_est_monthly']:8,} visits | alive={res['alive']} | kb={res['homepage_kb']:6} | links={res['internal_links']:4} | idx={res['indexed_pages_est']}")
        rand_sleep()

    # Save CSV
    fieldnames = ["domain","alive","homepage_kb","internal_links","indexed_pages_est","visitors_est_monthly"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvf:
        writer = csv.DictWriter(csvf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Done. Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

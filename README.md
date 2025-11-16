# WebMarketplaceScale

This project provides a Python script to analyze a large list of domains, check their availability, and generate a **heuristic-based estimate** of their monthly website visitors.

It is designed to process domains in batches from a simple text file and output a CSV file with the analysis. This is useful for "sizing" a potential market by getting a rough, relative comparison of traffic between many websites.

## Features

* **Batch Processing**: Processes a large list of domains in chunks using `START_INDEX` and `END_INDEX`.
* **Liveness Check**: Verifies if domains are "alive" (respond to HTTP/HTTPS requests).
* **Homepage Analysis**: Scrapes the homepage to measure its size (in KB) and count the number of internal links.
* **Visitor Estimation**: Uses a multi-factor heuristic to estimate monthly visitors.
* **Optional SERP API**: Can optionally use the Serper API for a more accurate estimation of a site's indexed pages.
* **Polite Scraping**: Includes a randomized polite delay between requests to avoid overwhelming servers.
* **CSV Output**: Saves all results in a clean, easy-to-use CSV file.

---

## How it Works

The script follows a clear pipeline for each domain it processes:

1.  **Read Input**: Reads the full list of domains from `azurl.txt`.
2.  **Slice List**: Selects only the domains between `START_INDEX` and `END_INDEX` to process.
3.  **Process Domain**: For each domain in the slice, it performs the following steps:
    * **Check Liveness (`domain_is_alive`)**: Sends an HTTP `HEAD` request to check for a successful response (status code < 400).
    * **Fetch Homepage (`fetch_homepage`)**: Fetches the full homepage HTML, calculates its size in KB, and parses it with BeautifulSoup.
    * **Count Links (`count_internal_links`)**: Scans the parsed HTML for `<a>` tags and counts how many point to the same domain (i.e., start with `/` or contain the domain name).
    * **Estimate Indexed Pages**: This is a crucial step with two possible methods:
        * **Method A (Default Heuristic)**: If `USE_SERP_API` is `False`, it uses `heuristic_indexed_pages` to *guess* the number of indexed pages based on homepage size and internal link count.
        * **Method B (SERP API)**: If `USE_SERP_API` is `True`, it calls the Serper API (`get_indexed_pages_via_serp`) to get the "About X results" for a `site:{domain}` Google search. This is generally more accurate.
    * **Estimate Visitors (`combine_into_visitors`)**: This function (explained below) takes all the gathered metrics (liveness, size, links, indexed pages) and combines them into a final monthly visitor estimate.
4.  **Save Output**: After processing all domains in the batch, the script writes all the results to the specified CSV file.

---

## 📈 How Monthly Visitors are Calculated

The estimation is a two-part heuristic. It first estimates a site's "size" (number of indexed pages) and then uses that to estimate traffic.

### Part 1: Estimating Indexed Pages

The script needs a way to guess how many pages a website has.

* **Default Heuristic (`heuristic_indexed_pages`)**: This method is a rough guess. It combines the **homepage size** (multiplied by `SIZE_KB_MULTIPLIER`) and the **square root of internal links** (multiplied by `LINKS_MULTIPLIER`). The logic is that larger homepages and more internal links often correlate with more total pages on the site.
* **SERP API (`get_indexed_pages_via_serp`)**: This is the preferred, more accurate method. It performs a `site:{domain}` search via the Serper API and scrapes the "About X results" count. This gives a real-world estimate of how many pages Google has indexed for that domain.

### Part 2: Estimating Monthly Visitors (`combine_into_visitors`)

Once the script has an `indexed_pages_est`, it plugs it into the final formula:

1.  A base "score" is calculated, starting with the `indexed_pages_est`.
2.  This score is increased based on the **homepage size** (a larger homepage suggests a more significant site).
3.  The score is increased again based on the **logarithm of internal links** (more links suggest more internal structure and authority).
4.  This final combined score is multiplied by `VISITORS_SCALE` (a calibration constant) to get the raw visitor number.
5.  A small amount of randomness (±10%) is applied to simulate natural variance.
6.  The result is clamped between `MIN_VISITORS` (1) and `MAX_VISITORS` (50,000,000).
7.  If the domain was found to be "dead" (`alive = False`), the final estimate is drastically reduced (multiplied by 0.05).

> ⚠️ **Disclaimer:** This is a very rough, unscientific heuristic. The resulting numbers are intended for **relative comparison** (e.g., "is Site A roughly 10x bigger than Site B?") and should **not** be treated as accurate, absolute, real-world analytics data.

---

## 🚀 How to Use

### 1. Prerequisites

You must have Python 3 installed.

### 2. Installation

1.  Clone this repository:
    ```bash
    git clone [https://github.com/SaidRafili/WebMarketplaceScale.git](https://github.com/SaidRafili/WebMarketplaceScale.git)
    cd WebMarketplaceScale
    ```
2.  Install the required Python libraries:
    ```bash
    pip install requests beautifulsoup4
    ```

### 3. Prepare Input File

Create or edit the `azurl.txt` file. Add one domain per line, without `http://` or `https://`.

**Example `azurl.txt`:**

### 4. Configure the Script

Open `size.py` in a text editor and adjust the variables in the configuration section at the top.

* `START_INDEX`: The line number to start processing from (e.g., `0` for the first line).
* `END_INDEX`: The line number to stop processing *before* (e.g., `100` to process the first 100 lines).
* `INPUT_FILE`: The name of your domain list file (default: `"azurl.txt"`).
* `OUTPUT_FILE`: The name for the resulting CSV file. It automatically includes the start/end index.
* `POLITE_DELAY`: The min/max time (in seconds) to wait between requests. Increase this if you get blocked or receive errors.
* `USE_SERP_API`: Set to `True` to use the Serper API for more accurate indexed page counts.
* `SERP_API_KEY`: **Required if `USE_SERP_API` is `True`**. Get your free or paid key from [serper.dev](https://serper.dev/) and paste it here.

### 5. Run the Script

Execute the script from your terminal:

```bash
python size.py

import re
import time
import random
import sys
from selenium import webdriver
import math
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import checkPotentialTable as ct
from http_request_randomizer.requests.proxy.requestProxy import RequestProxy
from pynput import keyboard
import datetime
import logging
logging.disable(sys.maxsize)
keys = []

def on_press(key):

    try:
        k = key.char
        if k == "q":
            keys.append(k)
            print("Exit Key Pressed: The program will quit after completing the current page")
        if k == "u":
            keys.append(k)

    except:
        return

listener = keyboard.Listener(on_press=on_press)
listener.start()

def handle_commands(of_interest,url,curr):
    if len(keys) != 0:
        command = keys[-1]
        if command == 'u':
            keys.clear()
            print(f"---------- Update : {datetime.datetime.now().strftime('%b-%d-%I%M%p-%G')} ----------")
            bio = url[url.index("%20") + 3:url.index("&sort")]
            print(f"Current Biomarker: {bio}")
            print(f"Current Page: {curr}")
            print(f"Rows Added This Iteration: {len(of_interest)}")
            print("-" * 50)
            print()
            return

def buildQuery(subject,biomarkers):

    base = "https://www.semanticscholar.org/search?year%5B0%5D=2019&year%5B1%5D=2020&q="
    filters = "&sort=relevance&pdf=true"
    query = [ subject+"%20"+term for term in biomarkers ]
    return [ base + query[i] + filters for i in range(0,len(query)) ]


def findArticles(url,curr,last_article):

    page_fault = 0
    driver.get(url)
    of_interest = []

    header = WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.dropdown-filters__result-count"))).text
    results = int(re.sub("[^0-9]", "", header))
    pages = math.ceil(results / 10)

    strt = curr
    while curr <= pages:
        data = []
        page = "&page=" + str(curr)

        try: # check if there are results on page, after page 100 they dont display any articles
            driver.get(url + page)
            articles = WebDriverWait(driver, 7).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.search-result-title")))

            for article in articles:
                handle_commands(of_interest,url,curr)
                title = article.text
                if (last_article and strt == curr) and title != last_article:
                    continue
                link = article.find_element_by_css_selector("a").get_attribute("href")
                data.append({"Title": title, "Link": link})

            for row in data:
                handle_commands(of_interest, url, curr)
                tables, pdf, journal = findTables(row["Link"])

                print(row["Link"])
                print("=====================")

                if tables:
                    row["Tables"] = tables
                else:
                    row["Tables"] = "Check PDF Later"

                row["PDF"] = pdf
                row["Journal"] = journal
                of_interest.append(row)

            if len(keys) != 0:
                page_fault = -1 * (curr + 1)
                break

        except TimeoutException:
            print("Last page: " + str(curr))
            break

        finally:
            curr += 1

    df = pd.DataFrame(data=of_interest, columns=["Title", "Link", "Tables", "PDF", "Journal"])
    return (df, page_fault)


def findTables(url):
    biomarkers = ["Monocytes and Sepsis"]
    keywords = ["machine learning","deep learning","predict","diagnostic"]
    driver.get(url)
    tables = []

    try:
        has_abstract = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.text-truncator.abstract__text.text--preline"))).text
    except TimeoutException: # if there is no abstract provided, use the title
        summary = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#paper-header > h1"))).text
    else: # some abstracts have a show more button
        try:
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.text-truncator__toggle.mod-clickable.more"))).click()
            summary = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.text-truncator.abstract__text.text--preline"))).text
        except:
            summary = has_abstract

    # dont consider irrelevant articles
    if len( [1 for item in biomarkers if item in summary.lower() ] ) == 0:
        return ("", "", "")

    try:
        figures = WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.figure-list__figure > a")))
    except:
        figures = []

    try:
        journal = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#paper-header > div.flex-row.paper-meta > li:nth-child(4) > span"))).text
    except:
        journal = "Unknown"

    try:
        pdf = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR,"div.alternate-sources-button.dropdown-button > a.icon-button.alternate-source-link-button"))).get_attribute("href")
    except:
        pdf = "Unknown"

    # still may have not direct link to pdf, just the original post on the home database
    if "pdf" not in pdf.lower():
        pdf = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.icon-button.button--full-width.button--primary"))).get_attribute("href")

    for fig in figures:
        if "table" in fig.text.lower():
            img = fig.find_element_by_css_selector("img").get_attribute("src")
            tables.append(img)

    if len(tables) == 0:
        return ("No tables found", pdf, journal)
    else:
        return (tables, pdf, journal)



def run_script(biomarkers):
    status = 0
    article_table = pd.DataFrame(columns=["Title","Link","Tables","PDF","Journal"])

    # if there was incomplete data, do that instead
    try:
        last = pd.read_csv("Incomplete.csv")
    except:
        search = buildQuery("COVID-19", biomarkers)
        start = [1] * len(search)
        last_article = ""
    else:
        search = list(last["Query"])
        start = list(last["Page"])
        article_table = pd.read_csv("SemanticScholarArticles.csv")
        last_article = list(article_table["Title"])[-1]
        article_table.drop(article_table.tail(1).index, inplace=True)

    for q in search:

        # for the incomplete data, there will be a page number to start from
        if start[search.index(q)] == 1:
            last_article = ""

        res, page_fault = findArticles(q,start[search.index(q)],last_article)
        article_table = article_table.append(res)

        # if there was an issue
        if page_fault != 0:
            error_query = [{"Query": q, "Page": abs(page_fault)}]
            queries_left = []


            if search[-1] != q:
                queries_left = [{"Query": query, "Page": 1} for query in search[search.index(q) + 1:]]
            output = pd.DataFrame(data=[*error_query, *queries_left])
            output.to_csv("Incomplete.csv", index=False)

            # if there was a keyboard interrupt, the page fault is negative
            if page_fault < 0:
                status = -2
            else:
                print("Repeated Failure to Connect to Server: No more articles can be read through this instance.")
                status = -1
            break

    article_table.drop_duplicates("Title")
    article_table.to_csv("SemanticScholarArticles.csv",index=False)
    driver.close()
    return status


def ChromeSetUp(path,PROXY):

    time.sleep(random.randint(3, 7))

    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    chrome_options.add_experimental_option("prefs", prefs)

    webdriver.DesiredCapabilities.CHROME['proxy'] = {
        "httpProxy": PROXY,
        "ftpProxy": PROXY,
        "sslProxy": PROXY,
        "proxyType": "MANUAL",
    }

    driver = webdriver.Chrome(executable_path=path, options=chrome_options)
    return driver


if __name__ == "__main__":

    # list of the biomarkers you want to search for
    biomarkers = ["procalcitonin"]
    MAXATTEMPTS = 5

    # This may have some legal/policy issues so we should check before the final paper is published
    # I think it's fine though
    # We should also consider iterating through IP Addresses for faster access
    req_proxy = RequestProxy()
    proxies = req_proxy.get_proxy_list()

    while len(proxies) < MAXATTEMPTS:
        proxies = [*proxies,req_proxy.get_proxy_list()]

    attempt = -1
    status = -1
    while (status == -1 and attempt < MAXATTEMPTS) or attempt == -1:
        attempt += 1
        print("Starting Up...\n")
        driver = ChromeSetUp("/Users/william/Desktop/chromedriver", proxies[attempt].get_address())
        status = run_script(biomarkers)


    if status == -2:
        print(f"\nScript was manually interrupted, last data obtained has been saved. \nThere were {attempt} interruption(s) from a repeated failed connection.")
    else:
        print(f"\nScript had {attempt} interruption(s) from a repeated failed connection. Maximum allowed is {MAXATTEMPTS}.\nIncomplete queries are saved in Incomplete.txt")


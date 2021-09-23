from pathlib import Path
import requests
import pandas as pd
import urllib.request
import os


# get pdf link based on the journal
def download_pdf(pdf_name,dest):
    url = ""
    if "PMC" in pdf_name:
        url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pdf_name}/pdf/"

    return save_pdf(pdf_name+".pdf",url,dest)


# save pdf into desired location
def save_pdf(name,pdf_link,dest):
    try:
        f = Path(f"{dest}/{name}")
        http_proxy = "http://10.10.1.10:3128"
        https_proxy = "https://10.10.1.11:1080"
        ftp_proxy = "ftp://10.10.1.10:3128"
        proxyDict = {
            "http": http_proxy,
            "https": https_proxy,
            "ftp": ftp_proxy
        }
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        r = requests.get(pdf_link, headers=headers, proxies=urllib.request.getproxies())

        if r.status_code == 200:
            f.write_bytes(r.content)
            return True

    except Exception as e:
        print(e)
        return False

    else:
        return False



def download_articles(dest,df_name,pdf=True,text=True,keep_pdf=False):
    df = pd.read_csv(df_name)

    if not (pdf or text):
        return

    for idx,row in df.iterrows():

        if pdf:
            status = download_pdf(row['PDF_File'],dest)

            if not status:
                df.loc[df["PDF_File"]==row['PDF_File'],"Error"] = "PDF Download"
                continue

    df.to_csv(df_name, index=False)


# run script
if __name__ == "__main__":

    download_dest = "TODO"
    df_name = "TBD_Download.csv"
    download_articles(download_dest,df_name,pdf=True,text=False,keep_pdf=True)
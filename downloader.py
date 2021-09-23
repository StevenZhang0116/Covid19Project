import requests
import urllib.request
from bs4 import BeautifulSoup as bsp
import pandas as pd
import os
import analyze_text as at

po_headers = {'User-Agent': 'User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}

def downloader(url, name):
	mount = requests.get(url,po_headers)
	with open(name, "wb") as code:
		code.write(mount.content)

def get_FileSize(filePath):
	fsize = os.path.getsize(filePath)
	return fsize
	

if __name__ == "__main__":
	df = pd.read_csv("./UniqueSemanticScholar.csv", encoding='ISO-8859-1')

	path = "./DownloadFiles"
	folder = os.path.exists(path)
	if not folder:
		os.makedirs(path)

	for i in range(54, 0, -1):
		pdf_url = df.at[i, "PDF"]
		pdf_name = "./DownloadFiles/" + df.at[i, "PDF_Name"]
		downloader(pdf_url, pdf_name)
		if get_FileSize(pdf_name) > 30000:
			print(i, pdf_url)
		else:
			print(i, pdf_url, pdf_name)
			os.remove(pdf_name)
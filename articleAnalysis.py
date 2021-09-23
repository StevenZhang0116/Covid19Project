import io
import os
import re
from os import listdir
from os.path import isfile, join
from pathlib import Path
import pandas as pd
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from pdfminer.pdfparser import PDFSyntaxError

# convert pdf to text
def extract_text(pdf_path):

    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    laparams = LAParams()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=laparams)
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    f = open(pdf_path, "rb")
    for idx,page in enumerate( PDFPage.get_pages(f, caching=True, check_extractable=True) ):
        if idx >= 7:
            break
        page_interpreter.process_page(page)
    text = fake_file_handle.getvalue().lower()

    return text


#  check specified keywords
def keyword_check(text):

    result = {}
    exclude_words = ['drug','treatment','anakinra']
    covid_keys = ['covid-19','sars-cov-2','2019-ncov']
    biomarker_keys = ['crp', 'c-reactive protein','d-dimer','procalcitonin','pct']
    other_keys = ['dental', 'dentistry']
    # other_keys = ['meta-analysis', 'systematic review', 'score', 'auroc', 'auc',
    #         'clinical characteristics', 'clinical performance','clinical course',
    #         'clinical features', 'risk factor', 'model', 'diagnosis', 'diagnostic',
    #         'hematologic parameters', 'hematologic features', 'hematologic panel',
    #         'machine learning', 'severity', 'predict']
    exclusion = {"covid": "Not COVID Related", "additional": "Not Dental Related"}
    # exclusion = {"covid": "Not COVID Related", "biomarker": "No Specified Biomarkers",
    #              "additional": "No additional keywords", 'unwanted drug': "Mention of unwanted drug class"}

    result['covid'] = 1 if [1 for key in covid_keys if key in text] else 0
    # result['biomarker'] = 1 if [1 for key in biomarker_keys if key in text] else 0
    result['additional'] = 1 if [1 for key in other_keys if key in text.split()] else 0
    # result['unwanted drug'] = 0 if re.search(r"mab(?![a-zA-Z0-9])",text) else 1

    comment = [ exclusion[category] for category,val in result.items() if not val ]

    return comment if comment else ["N/A"]


# identify biomarkers used
def check_biomarkers(text):

    biomarker_keys = { "CRP": ['crp', 'c-reactive protein'], "D-Dimer": ["d-dimer"], "Procalcitonin": ['procalcitonin','pct'] }
    biomarkers = [ key for key,val in biomarker_keys.items() if [ ele for ele in biomarker_keys[key] if ele in text] ]

    return biomarkers if biomarkers else ['N/A']


# analyze pdf to specifications
def check_pdf(pdf,biomarker, exclusion):

    if not biomarker and not exclusion:
        print("A category must be specified")
        return

    try:
        text = extract_text(pdf)

    except Exception as e:
        raise e

    result = {}

    if biomarker:
        result['Biomarkers'] = check_biomarkers( text )

    if exclusion:
        result["Exclusion_Reason"] = keyword_check( text )

    return result



if __name__ == "__main__":


    df = pd.read_csv("/Users/william/Desktop/UniqueSemanticScholar.csv")
    path = "/Users/william/Desktop/McDevitt/COVID/Article_Search/SemanticScholar"
    pdf_list = [ f for f in listdir(path) if isfile( join(path, f) ) and f.endswith(".pdf") ]

    table = {}

    for pdf in pdf_list:

        try:
            new_cols = check_pdf( join(path, pdf), biomarker=True, exclusion=True )
            col_names = list( new_cols.keys() )

        except PDFSyntaxError:
            new_cols = { col: ["PDF Issue"] for col in col_names}

        except Exception as e:
            new_cols = {col: ["Other Error"] for col in col_names}
            print(e)

        finally:
            table[pdf] = new_cols

    for col in col_names:
        df[col] = df["PDF_Name"].map( { k: table[k][col] for k,v in table.items() } )
    #
    df.to_csv("DentalCovid.csv",index=False)
"""
Download pdfs, create text, write back results
"""
from useful_grid import QuickGrid
import os
import urllib.request
from urllib.parse import urlparse
import json
import unicodedata
import sys
import time
import pdfplumber

from .analysis import process_text
from .tests import run_tests

pdf_dir = "pdfs"
json_dir = "json"
data_dir = "data"

tbl = dict.fromkeys(
    i for i in range(sys.maxunicode) if unicodedata.category(chr(i)).startswith("P")
)


def fix_formatting(r):
    r = r.replace("\uf0b7", "")
    r = r.replace("Novembers", "November")
    return r


def lines_to_sentences(rows):
    for r in lines_to_sentences_inner(rows):
        for s in r.split(". "):
            s = remove_punctuation(s.strip())
            s = s.replace("  ", " ")
            if s:
                yield s


def lines_to_sentences_inner(rows):
    current = ""
    numbered_start = ["{0}. ".format(x) for x in range(1, 50)]

    for r in rows:
        s_r = r.strip().lower()
        if len(s_r) == 1:
            continue
        words = s_r.split(" ")
        words = [x for x in words if x]
        if len(words) == 2:
            if "reference" in s_r:
                continue
        r = fix_formatting(r)
        for n in numbered_start:
            if r[: len(n)] == n:
                yield current
                current = ""
                break
        current += r
        if current.strip() and current.strip()[-1] == ".":
            yield current
            current = ""
    if current:
        yield current


def remove_punctuation(text):
    return text.translate(tbl)


def pdf_from_filename(x):
    """
    where are pdfs stored
    """
    return os.path.join(pdf_dir, x)


def json_from_filename(x):
    """
    where are json stored
    """
    return os.path.join(json_dir, os.path.splitext(x)[0] + ".json")


def iter_over_filenames(quarter=None):
    qg = QuickGrid().open([data_dir, "ICO clean.xlsx"], tab="2015-20")
    qg.data = qg.data
    if quarter:
        start = (len(qg) / 4 * int(quarter)) - 10
        if start < 0:
            start = 0
        end = (len(qg) / 4 * (int(quarter) + 1)) + 10
    else:
        start = 0
        end = len(qg) + 10
    for n, r in enumerate(qg):
        if n < start or n > end:
            continue
        url = r["url"]
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        print(filename)
        yield filename, url

def download_pdfs():
    for filename, url in iter_over_filenames():
        pdf_path = pdf_from_filename(filename)
        if os.path.exists(pdf_path) is False:
            print(url)
            urllib.request.urlretrieve(url, pdf_path)
            time.sleep(5)


def process_text_to_json():
    for filename, url in iter_over_filenames():
        pdf_path = pdf_from_filename(filename)
        json_path = json_from_filename(filename)
        if filename:
            if not os.path.exists(json_path) and os.path.exists(pdf_path):
                try:
                    read_text(filename)
                except Exception:
                    continue


def read_text(filename):
    pdf_path = pdf_from_filename(filename)
    json_path = json_from_filename(filename)
    pdf = pdfplumber.open(pdf_path)
    results = {"source": {}, "analysis": {}}
    for n, page in enumerate(pdf.pages):
        page = pdf.pages[n]
        text = page.extract_text()
        results["source"][n] = text
    pdf.close()
    with open(json_path, "w", encoding="utf8") as json_file:
        json.dump(results, json_file)


class Decision(object):

    """
    Decision objects control the ongoing information about
    a decisions processing and status
    """

    def __init__(self, filename):
        self._data = None
        self.rows = None
        self.results = {}
        self.errors = {}
        self.filename = filename
        self.load_text()

    def load_text(self):
        json_path = json_from_filename(self.filename)
        rows = []
        with open(json_path, "r", encoding="utf8") as json_file:
            self._data = json.load(json_file)
            data = self._data["source"]
            for x in range(0, 100):
                if str(x) in data:
                    page = data[str(x)]
                    if page:
                        rows.extend(page.split("\n"))
        self.rows = list(lines_to_sentences(rows))
        self.results = self._data.get("results", {})
        self.errors = self._data.get("errors", {})

    def save(self):
        self._data["results"] = self.results
        self._data["errors"] = self.errors
        json_path = json_from_filename(self.filename)
        with open(json_path, "w", encoding="utf8") as json_file:
            json.dump(self._data, json_file)

    def process(self, debug=False):
        self.results = process_text(self.filename, self.rows, debug)
        self.errors = run_tests(self.results)

        dates = [
            "start_date",
            "review_date",
            "review_reply_date",
            "ico_date",
        ]

        for d in dates:
            if self.results[d]:
                self.results[d] = self.results[d].isoformat()
            else:
                self.results[d] = None

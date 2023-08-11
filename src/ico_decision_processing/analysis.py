"""
Analyse the body of a decision to extract wanted properties
"""

from datetime import datetime
import string
import calendar
from useful_grid import QuickGrid
import unicodedata
import sys

tbl = dict.fromkeys(
    i for i in range(sys.maxunicode) if unicodedata.category(chr(i)).startswith("P")
)


def remove_punctuation(text):
    return text.translate(tbl)


months = [x.lower() for x in calendar.month_name[1:]]


common_words = set(
    [
        "the",
        "be",
        "to",
        "of",
        "it",
        "and",
        "a",
        "in",
        "that",
        "have",
        "i",
        "an",
        "for",
        "its",
        "further",
    ]
)


def remove_common_words(s):
    words = s.split(" ")
    words = [x for x in words if x not in common_words]
    return " ".join(words)


class KeyWord(object):
    """
    local storage for external keyword file
    """

    storage = {}
    tab = "keywords"

    @classmethod
    def conform(cls, v):
        sv = v.strip().lower()
        if sv != "respond to the request":
            return remove_common_words(sv)
        else:
            return sv

    @classmethod
    def load(cls):
        qg = QuickGrid().open("data//keywords.xlsx", tab=cls.tab)
        cls.storage[cls.tab] = [[cls.conform(x[0]), x[1]] for x in qg.data]

    @classmethod
    def keywords(cls):
        if cls.tab not in cls.storage:
            cls.load()
        return cls.storage[cls.tab]

    @classmethod
    def get_keywords(cls, flag):
        return [x for x, y in cls.keywords() if y == flag]


class IDFlag(KeyWord):
    tab = "id_flags"

    @classmethod
    def conform(cls, v):
        return v


def check_keywords(rows, debug):
    """
    see if there's a keyword match for known flags
    """
    flags = []
    keywords = KeyWord.keywords()
    for r in rows:
        lr = r.lower()
        if "respond to the request" not in lr:
            lr = remove_common_words(lr)
        for k, f in keywords:
            if k in lr:
                flags.append(f)
                if debug:
                    print("Flag {0}: {1} found in {2}".format(f, k, lr))
    return flags


def check_ids(filename):
    """
    see if there's a keyword match for known flags
    """
    flags = []
    keywords = IDFlag.keywords()
    for k, f in keywords:
        if k == filename:
            flags.append(f)
    return flags


def multi_date_extract(v):
    result = True
    responses = []
    skip_n = -1
    while result is not None:
        result, skip_n = simple_date_extract(v, skip_n)
        if result:
            responses.append(result)
    return responses


def simple_date_extract(v, skip_past_n=0):
    """
    extract a date from a sentence
    """
    v = v.replace("<p>", "")
    v = v.replace("</p>", "")
    v = v.replace(",", " ")
    words = v.split(" ")
    if words and words[-1].lower() in months:
        words.append("")
    for n, x in enumerate(words):
        if n <= skip_past_n:
            continue
        if x.lower() in months and len(words) > n + 1:
            date = words[n - 1]
            year = words[n + 1]
            year = "".join([x for x in year if x not in string.punctuation])

            # little catch for weird lists of months

            if year in months:
                continue

            if len(year) > 4:
                year = year[:4]

            fake_year = False

            try:
                int(year)
            except Exception:
                fake_year = True
                # not a year, but is a date, substituing
                year = "1900"

            if year[:2] == "21":  # try and catch reverse typo
                year = "201" + year[-1]

            date = date.replace("st", "")
            date = date.replace("rd", "")
            date = date.replace("th", "")
            if len(date) == 1:
                date = "0" + date

            fake_date = False
            try:
                int(date)
            except Exception:
                date = "01"
                fake_date = True

            if fake_date and fake_year:  # canot infer both
                return None, n

            t = " ".join([date, x, year])
            while t and t[-1] in string.punctuation:
                t = t[:-1]
            try:
                dt = datetime.strptime(t, "%d %B %Y")
                if fake_date:
                    # use hour marker to say when these are fake dates
                    dt = dt.replace(hour=1)
                return dt, n
            except ValueError:
                return None, n
    return None, 0


def guess_year_from_previous(current, last):
    """
    assumes the new date is after the last date
    """
    current = current.replace(year=last.year)
    if last > current:
        current = current.replace(year=current.year + 1)
    return current


def fix_dates(dates, debug=False):
    last = None
    results = []
    for n, d in enumerate(dates):
        if d.year == 1900 and last:
            replaced = guess_year_from_previous(d, last)
            results.append([d, replaced])
            last = replaced
        else:
            last = d
            if (
                n == 0
            ):  # if the very first date, set back a year so it is not seen as the 'start' because this tends to be the offical date
                try:
                    last = last.replace(year=last.year - 1)
                except ValueError:
                    # when you've created an invalid date
                    pass
            results.append([d, d])
        if debug:
            print(results[-1])
    return results


def get_all_dates(rows, debug):
    results = []
    for r in rows:
        lr = r.lower()
        dates = multi_date_extract(lr)
        results.extend(dates)
    return fix_dates(results, debug)


class DateExtract(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.score = 0


def first_date_after_trigger(
    rows, flag, debug, attention_score=8, prefer_real=True, stop_word=""
):
    triggers = KeyWord.get_keywords(flag)
    pay_attention = 0
    dates = []
    date_count = 0
    for t in triggers:
        for r in rows:
            lr = r.lower()
            lr = remove_common_words(lr)
            lr = "".join([x for x in lr if x not in string.punctuation])
            if stop_word and stop_word in lr:  # trigger to stop and go no further
                continue
            if t.lower().strip() in lr:
                pay_attention = attention_score  # detect in the next 2
            if pay_attention:
                extracted_dates = multi_date_extract(lr)
                pay_attention -= 1
                if extracted_dates:
                    if debug:
                        print("triggered by: {1}: {0}".format(t, flag))
                        print(extracted_dates)
                    for d in extracted_dates:
                        date_count += 1
                        de = DateExtract(count=date_count, date=d, line=lr)
                        dates.append(de)
    if dates:
        if prefer_real:
            if len(set([x.date.hour for x in dates])) > 1:  # both real and fake dates
                # prefer real
                dates = [x for x in dates if x.date.hour == 0]
        return dates
    return dates


def process_text(filename, rows, debug=False):
    """
    analyse text and run texts
    """
    all_dates = get_all_dates(rows, debug)
    replacement_lookup = {x[0]: x[1] for x in all_dates}

    results = {"id": filename}

    def fix_bad_date(date):
        # use first date if multiple
        if date:
            date = date[0].date
        if date and date.year == 1900:
            replacement = replacement_lookup[date]
            print(
                "replacing {0} with {1}".format(
                    date.isoformat(), replacement.isoformat()
                )
            )
            return replacement_lookup[date]
        else:
            return date

    if debug:
        for r in rows:
            try:
                print(r)
            except Exception:
                pass

    # get set of possible responses based on flags
    start_dates = first_date_after_trigger(
        rows, "start_date_trigger", debug, prefer_real=False
    )
    review_dates = first_date_after_trigger(rows, "ir_asked_date", debug)
    review_reply_dates = first_date_after_trigger(rows, "ir_reply_date", debug)
    ico_dates = first_date_after_trigger(
        rows,
        "ico_date_trigger",
        debug,
        prefer_real=False,
        attention_score=4,
        stop_word="reasons_for_decision",
    )

    # try and sort out competing start dates
    if len(start_dates) > 1:
        for d in start_dates:
            if "the complainant" in d.line:
                d.score += 5
            if "decision notice" in d.line:
                d.score -= 1
            if d.date.hour == 1:
                d.score -= 1
            if d.date.year < 2010:
                d.score -= 20

        # prefer first if two have the same score
        start_dates.sort(key=lambda x: x.count)
        start_dates.sort(key=lambda x: x.score, reverse=True)

        start_dates = start_dates[:1]

    # adjust ICO dates based on known start dates
    if start_dates:
        # only dates after start date
        ico_dates = [x for x in ico_dates if x.date > start_dates[0].date]
        # if multiple dates, prefer full date
        if len(set([x.date.hour for x in ico_dates])) > 1:
            ico_dates = [x for x in ico_dates if x.date.hour == 0]

    if review_dates and start_dates:
        review_dates = [x for x in review_dates if x.date > start_dates[0].date]

    review_dates = [x for x in review_dates if x.date.year > 2010]

    review_dates = [
        x
        for x in review_dates
        if x.date not in [y.date for y in review_reply_dates + start_dates + ico_dates]
    ]
    review_reply_dates = [
        x for x in review_reply_dates if x.date not in [y.date for y in start_dates]
    ]  # can get return and escalate to ICO same day

    # if multiple options make coherent
    if review_dates and review_reply_dates:
        # can't overlap
        review_dates = [x for x in review_dates if x.date < review_reply_dates[0].date]

    results["start_date"] = fix_bad_date(start_dates)
    results["review_date"] = fix_bad_date(review_dates)
    results["review_reply_date"] = fix_bad_date(review_reply_dates)
    results["ico_date"] = fix_bad_date(ico_dates)
    results["flags"] = check_keywords(rows, debug) + check_ids(filename)

    return results


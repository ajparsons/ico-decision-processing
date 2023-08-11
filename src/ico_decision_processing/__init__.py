import os
from .file_operations import Decision, iter_over_filenames, json_from_filename, data_dir
from .tests import valid_tests
from useful_grid import QuickGrid
from optparse import Values

from urllib.parse import urlparse
import datetime
from _tracemalloc import start
from _ast import If


def process_decisions(force=False, quarter=None):
    print("quarter")
    print(quarter)
    for filename, url in iter_over_filenames(quarter=quarter):
        if os.path.exists(json_from_filename(filename)):
            process_decision(filename, force=force)


def process_decision(filename, debug=False, force=False):
    d = Decision(filename)
    if not d.results or d.errors or force:
        d.process(debug)
        for k, v in d.results.items():
            if "date" in k and v:
                nv = get_dt(v).strftime("%d %B %y")
            else:
                nv = v
            print("{0}: {1}".format(k, nv))
        print(d.results)
        print(d.errors)
        d.save()
    else:
        print("results processed, skipping")


def export_errors():
    qg = QuickGrid(header=["id"])

    for t in valid_tests:
        qg.header.append(t.explanation)

    qg.header.append("error_total")

    for filename, url in iter_over_filenames():
        if os.path.exists(json_from_filename(filename)):
            d = Decision(filename)
            row = [d.filename]
            total = 0
            print(d.errors)
            for t in valid_tests:
                if t.explanation in d.errors:
                    row.append(1)
                    total += 1
                else:
                    row.append(0)

            row.append(total)
            qg.add(row)

    qg.save([data_dir, "errors.csv"], force_unicode=True)


def fix_date(v):
    if v:
        return v.split("T")[0]
    else:
        return ""


def get_dt(v):
    v = fix_date(v)
    dt = datetime.datetime.strptime(v, "%Y-%m-%d")
    return dt


def export_data():
    qg = QuickGrid(header=["decision_file"])

    values = [
        "start_date",
        "ico_date",
        "date_diff",
        "review_date",
        "review_reply_date",
        "review_data_either",
        "likely_invalid_ir_date",
        "substantive_response",
        "issue_response",
        "valid_refusal",
        "fresh_response",
        "steps_to_comply",
        "does_not_require",
        "section_54",
        "flags",
    ]

    qg.header.extend(values)

    flags = [
        "substantive_response",
        "issue_response",
        "valid_refusal",
        "fresh_response",
        "steps_to_comply",
        "does_not_require",
        "section_54",
    ]

    for filename, url in iter_over_filenames():
        if os.path.exists(json_from_filename(filename)):
            d = Decision(filename)
            row = [d.filename]
            if "Request passed before to ICO before made" in d.errors:
                row.append("")
                row.append("")
            else:
                row.append(fix_date(d.results["start_date"]))
                row.append(fix_date(d.results["ico_date"]))

            if d.results["start_date"] and d.results["ico_date"]:
                start = get_dt(d.results["start_date"])
                end = get_dt(d.results["ico_date"])
                delta = end - start
                delta = delta.days
                if delta < 0:
                    delta = 0
                row.append(delta)
            else:
                row.append("")

            row.append(fix_date(d.results["review_date"]))
            row.append(fix_date(d.results["review_reply_date"]))

            # get the combined
            if d.results["review_reply_date"]:
                row.append(fix_date(d.results["review_reply_date"]))
            else:
                row.append(fix_date(d.results["review_date"]))

            if "no_ir_date" in d.results["flags"]:
                row.append("1")
            else:
                row.append("")

            for f in flags:
                if f in d.results["flags"]:
                    row.append("1")
                else:
                    row.append("")

            unique_flags = list(set(d.results["flags"]))
            unique_flags.sort()
            row.append(",".join(unique_flags))
            if "ignore_processing" not in unique_flags:
                qg.add(row)

    qg.save([data_dir, "results.csv"], force_unicode=True)


def join_data():
    results = QuickGrid().open([data_dir, "results.csv"], force_unicode=True)
    results_lookup = {x[0]: x[1:] for x in results.data}

    qg = QuickGrid().open([data_dir, "ICO clean.xlsx"], tab="2015-20")
    qg.header = qg.header[:16]
    qg.header.extend(results.header[1:])
    new_data = []
    for r in qg.data:
        r = r[:16]
        url = r[-1]
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        new_cols = results_lookup.get(filename, ["", "", "", "", "", ""])
        r.extend(new_cols)
        new_data.append(r)

    qg.data = new_data

    qg.save([data_dir, "ico_updated_with_dates.csv"], force_unicode=True)


def make_completeness():
    results = QuickGrid().open([data_dir, "results.csv"], force_unicode=True)

    values = results.header[1:-1]

    qg = QuickGrid(header=["value", "total", "%"])

    for v in values:
        count = len([x[v] for x in results if x[v]])
        percentage = round((count / float(len(results))) * 100, 2)
        qg.add([v, count, percentage])

    qg.save([data_dir, "completeness.csv"], force_unicode=True)

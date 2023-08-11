"""
invoke tasks files

"""
from invoke import task

from ico_decision_processing import (
    process_decisions,
    export_errors,
    export_data,
    join_data,
    make_completeness,
)
from ico_decision_processing.file_operations import download_pdfs, process_text_to_json


@task
def process(c, force=False, quarter=None):
    process_decisions(force=force, quarter=quarter)


@task
def errors(c):
    export_errors()


@task
def results(c):
    export_data()
    join_data()
    make_completeness()


@task
def downloadpdfs(c):
    download_pdfs()


@task
def json(c):
    process_text_to_json()

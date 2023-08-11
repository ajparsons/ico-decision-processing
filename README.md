# ICO decision processor

[Not maintained, uploading old code so flags etc can be reused]

Analysis to process ICO decision notices for openDemocracy's Art of Darkness report. 

This is a process to extract various dates (and other information) from ICO decision notices. 

Several flags are used as triggers for date collection, with additional tests 

Flags are triggered by phrases stored in `data/keywords.xlsx`.

## Reviewing this to use elsewhere

Assuming this is just being raided to build another scraper, here are the key bits.

The key list of flags is in `data/keywords.xlsx` - this is probably the most helpful file.

A few bits in `analysis.py` are also useful - the `first_date_after_trigger` function is used 
to extract the first date after a specific set of keyphrases was used. As I remember, this was to make it more flexible with changes over time.

A lot of the logic here is trying to get the dates in a logical order - but it's also reacting to edge cases that might be processed this time, and there might be new edge cases that need new work. 

The `tests.py` was used for integrity checking the results - making sure that expected properties were found together to debug and adjust the scraper.   

My *hope* would be that building something to scrape the last few years could be a lot less complicated - as there is less variation than there is over all time. 

## Use

Requires python and poetry to be installed.  

Then `poetry run invoke ...` to run invoke commands below. 

The core data is expected in `data/ICO clean.xlsx`.

### To set up the data

- `invoke downloadpdfs` - will download all pdfs mentioned in `data/ICO clean.xlsx`. 
- `invoke json` - will extract the text to create json files. 
- `invoke process` - will apply the analysis and tests to the json files and export documents. 

By default, will only run on those with no prior analysis or with current errors. `invoke process --force` will rerun on all. 

- `invoke errors`  - Export errors document (documents that failed described tests) - `data/errors.csv`
- `invoke results` - Create results document, merges listed results with `clean ico.xlsx`

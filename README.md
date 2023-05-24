# Cirruswiki: Efficiently Handling CirrusSearch Wikipedia Dumps

Cirruswiki (CirrusSearch Wikipedia Processor)  Python script designed to efficiently handle CirrusSearch Wikipedia dumps. 

It is used to download, extract data from the dumps, process it with both a cleaner which is heavily inspired from the [WikiExtractor](https://github.com/attardi/wikiextractor) and a tokenizer, and finally index them with [Elasticsearch](https://www.elastic.co/products/elasticsearch).


## Usage

```bash
usage: python cirrus_extractor.py [-h] [--link LINK] [--lang LANG]
                           [--latest | --no-latest] [--process | --no-process]
                           [--output OUTPUT] [--index INDEX]
                           [--debug | --no-debug] [--verbose | --no-verbose]

options:
    -h, --help            show this help message and exit
    --link LINK           Download link
    --lang LANG           Language code
    --latest, --no-latest
                        Download latest dump
    --process, --no-process
                        Process the dump
    --output OUTPUT       Output directory
    --index INDEX         Index name to store the data in Elasticsearch
    --debug, --no-debug   Debug output
    --verbose, --no-verbose
                        Verbose output

```

## Example
Here are a couple of examples demonstrating how to use Cirruswiki effectively:

1. Downloading a specific Cirrus dump (e.g., German Wikipedia dump from 2023-05-15), processing it, and indexing it in the Elasticsearch index `dewiki`:

```bash
python cirrus_extractor.py \
        --link https://dumps.wikimedia.org/other/cirrussearch/current/dewiki-20230515-cirrussearch-content.json.gz \
        --process \
        --index dewiki \
        --output output \
        --verbose
```

2. Downloading the latest Cirrus dump (e.g., French Wikipedia dump), processing it, and indexing it in the Elasticsearch index `frwiki` (with debugging enabled):

```bash
python cirrus_extractor.py \
        --lang fr \
        --latest \
        --process \
        --index frwiki \
        --output output \
        --debug
```

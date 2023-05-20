import argparse
import logging
import os

from cirrus_download import CirrusDownloader
from cirrus_indexer import CirrusElasticsearchIndexer
from cirrus_preprocess import CirrusPreprocess

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Download Wikipedia dump")

    argparser.add_argument("--link", help="Download link")
    argparser.add_argument("--lang", default="en", help="Language code")
    argparser.add_argument(
        "--latest", action=argparse.BooleanOptionalAction, help="Download latest dump"
    )
    argparser.add_argument(
        "--process",
        action=argparse.BooleanOptionalAction,
        help="Process the dump",
    )
    argparser.add_argument("--output", default="data", help="Output directory")
    argparser.add_argument(
        "--index", help="Index name to store the data in Elasticsearch"
    )
    argparser.add_argument(
        "--debug", action=argparse.BooleanOptionalAction, help="Debug output"
    )
    argparser.add_argument(
        "--verbose", action=argparse.BooleanOptionalAction, help="Verbose output"
    )
    args = argparser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    if args.index is None:
        print("No Index Name Provided For Elasticsearch, Skipping Indexing")

    ########################################
    # Download the dump
    ########################################

    downloader = CirrusDownloader(lang=args.lang)

    if args.link:
        downloader.download_file(args.link, args.output)
    elif args.latest:
        downloader.download_latest_dump(args.output)
    elif args.link is None and args.latest is None:
        raise ValueError("Please provide a link or set --latest to True")

    filename = downloader.decompress_wikidump()

    ########################################
    # Extract the dump
    ########################################

    if args.process:
        preprocessor = CirrusPreprocess(model_name="bert-base-uncased")
        extractedfile_path = preprocessor.tokenize_dump(filename, args.output)

    ########################################
    # Index the dump
    ########################################

    if args.index:
        indexer = CirrusElasticsearchIndexer(index_name=args.index)
        indexer.index_file(extractedfile_path)

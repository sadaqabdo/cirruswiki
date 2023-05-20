"""
Python script to download, extract, segment and index Wikipedia dump using Elasticsearch.
"""

import logging
import os
import subprocess
from typing import Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://dumps.wikimedia.org/other/cirrussearch/current/"


class CirrusDownloader:
    """
    Class to download and extract Wikipedia dump

    Args:
        lang (str, optional): language code. Defaults to "en".
        subset (str, optional): subset of the dump. Defaults to "content".
        filename (str, optional): filename to save to. Defaults to None.
        output (str, optional): output directory. Defaults to "data".
        decompress (bool, optional): whether to decompress the dump. Defaults to True.

    Raises:
        ValueError: if no dump link is found for the given language and subset
        ValueError: if filename is not provided
        ValueError: if file extension is not supported
        RuntimeError: if download fails for any reason

    Examples:
        >>> downloader = CirrusDownloader(lang="en", subset="content")
        >>> downloader.download_file("https://dumps.wikimedia.org/other/cirrussearch/current/enwiki-20210501-cirrussearch-content.json.gz")
        >>> downloader.decompress_wikidump()

        >>> downloader = CirrusDownloader(lang="en", subset="content")
        >>> downloader.download_latest_dump()
        >>> downloader.decompress_wikidump()

        >>> downloader = CirrusDownloader(lang="en", subset="content")
        >>> downloader.download_latest_dump()
        >>> downloader.decompress_wikidump()
    """

    def __init__(
        self,
        lang: str = "en",
        subset: str = "content",
        filename: Optional[str] = None,
        output: str = "wikicirrus",
    ):
        """
        Initialize CirrusDownloader

        Args:
            lang (str, optional): language code. Defaults to "en".
            subset (str, optional): subset of the dump. Defaults to "content".
            output (str, optional): output directory. Defaults to "data".
        """

        self.lang = lang
        self.subset = subset
        self.filename = filename
        self.output = output

    def download_file(self, link: str, output: Optional[str] = None):
        """
        Download file from link and save it to filename

        Args:
            link (str): url to download from
            filename (str): filename to save to

        Raises:
            RuntimeError: if download fails for any reason
        """

        if self.lang is None:
            self.lang = link[:2]

        if output is not None:
            self.output = output
            if not os.path.exists(self.output):
                os.makedirs(self.output)

        if self.filename is None:
            self.filename = os.path.join(self.output, link.split("/")[-1])

        try:
            logging.info(
                "Downloading %s",
            )
            subprocess.check_call(["wget", "-O", self.filename, link])
            return self.filename
        except subprocess.CalledProcessError as exc:
            logging.error("Failed to download %s", link)
            raise RuntimeError(f"Failed to download {link}") from exc

    def get_latest_dump(self, lang="en", subset="content"):
        """
        Get the latest dump link from Wikimedia

        Args:
            lang (str, optional): language code. Defaults to "en".

        Returns:
            str: link to the latest dump
        """

        wikilang = lang + "wiki-"

        response = requests.get(BASE_URL, timeout=5)
        content = response.text

        soup = BeautifulSoup(content, "html.parser")
        links = soup.find_all("a")

        for dump_link in links:
            href = dump_link.get("href")
            if wikilang in href and subset in href:
                return BASE_URL + href

        raise ValueError(f"No dump link found for {lang}-{subset}")

    def download_latest_dump(self, output: Optional[str] = None):
        """
        Download the latest dump

        Returns:
            str: filename of the downloaded dump
        """
        if output is not None:
            self.output = output
            if not os.path.exists(self.output):
                os.makedirs(self.output)

        link = self.get_latest_dump(self.lang, self.subset)
        return self.download_file(link, self.output)

    def decompress_wikidump(self, filename: Optional[str] = None):
        """
        Decompress the wiki dump file

        Args:
            filename (str): filename to decompress

        Returns:
            str: decompressed filename
        """
        if filename is None:
            filename = self.filename
            if filename is None:
                raise ValueError("Filename not provided")

        logging.info("Extracting %s", filename)

        file_extension = self.filename.split(".")[-1]
        if file_extension == "bz2":
            subprocess.check_call(["bzip2", "-d", filename])
        elif file_extension == "gz":
            subprocess.check_call(["gunzip", "-d", filename])
        else:
            raise ValueError(f"Unknown file extension: {file_extension}")

        return filename[: -len(file_extension) - 1]

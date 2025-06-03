import json
from typing import Optional

from elasticsearch import Elasticsearch, helpers


class CirrusElasticsearchIndexer:

    """
    Class to index Cirrus Wikipedia dump in Elasticsearch

    Args:
        index_name (str): name of the index to store the data in Elasticsearch
        doc_store (Elasticsearch, optional): Elasticsearch doc store. Defaults to None.
        username (str, optional): username for Elasticsearch. Defaults to "elastic".
        password (str, optional): password for Elasticsearch. Defaults to None.
        ca_certs (str, optional): path to CA certificates. Defaults to None.
        verify_certs (bool, optional): whether to verify certificates. Defaults to None.

    Examples:
        >>> indexer = CirrusElasticsearchIndexer(index_name="wikicirrus")
        >>> indexer.index_file("wikicirrus/enwiki-20210501-cirrussearch-content.json")
    """

    def __init__(
        self,
        index_name: str,
        doc_store=None,
        username: Optional[str] = "elastic",
        password: Optional[str] = None,
        ca_certs: Optional[str] = None,
        verify_certs: Optional[bool] = None,
    ):
        """
        Initialize CirrusELasticsearchIndexer

        Args:
            index (str): name of the index to store the data in Elasticsearch
        """

        self.index_name = index_name
        self.doc_store = doc_store or self._init_doc_store()
        self.username = username
        self.password = password
        self.ca_certs = ca_certs
        self.verify_certs = verify_certs

    def _init_doc_store(self):
        """
        Initialize Elasticsearch doc store
        """

        if self.username and self.password:
            doc_store = Elasticsearch(
                "https://localhost:9200",
                http_auth=(self.username, self.password),
                ca_certs=self.ca_certs,
                verify_certs=True,
                index=self.index_name,
            )
        else:
            doc_store = Elasticsearch(
                "http://localhost:9200",
                timeout=60,
                max_retries=10,
                retry_on_timeout=True,
                index=self.index_name,
            )

        if not self.doc_store.ping():
            raise RuntimeError("Elasticsearch is not running!")

        return doc_store

    def index(self, data):
        """
        Index data into Elasticsearch

        Args:
            data (dict): data to be indexed
        """

        helpers.bulk(self.doc_store, data, index=self.index_name, batch_size=20_000)
        self.doc_store.indices.refresh(index=self.index_name)
        stats = self.doc_store.indices.stats(index=self.index_name)
        stats = stats["_all"]["primaries"]["docs"]["count"]
        print("Indexed %s docs with Elasticsearch", len(data))
        print("Total docs in index: %s", stats)

    def index_file(self, filepath):
        """
        Iterate over the file and index its contents into Elasticsearch index

        Args:
            data (dict): data to be indexed
        """

        with open(filepath, "r", encoding="utf-8") as f:
            articles = []

            for line in f:
                try:
                    data = json.loads(line)
                except json.decoder.JSONDecodeError:
                    print("JSONDecodeError while reading line to index")
                    continue

                articles.append(data)

                if len(articles) == 1_000_000:
                    self.index(articles)
                    articles = []

            self.index(articles)

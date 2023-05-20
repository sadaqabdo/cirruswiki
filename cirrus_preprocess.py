import json

from tqdm.auto import tqdm
from transformers import AutoTokenizer

from cirrus_clean import clean, normalize_title


class CirrusPreprocess:
    """
    Class to preprocess an Article of the Cirrus wiki dump

    Args:
        model_name (str): name of the model to use for tokenization

    Examples:
        >>> preprocess = CirrusPreprocess(model_name="bert-base-uncased")
        >>> preprocess.tokenize_content(article)
    """

    def __init__(self, model_name: str):
        """
        Initialize CirrusPreprocess

        Args:
            model_name (str): name of the model to use for tokenization
        """

        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize_content(self, article: dict):
        """
        Tokenize the article content using the tokenizer

        Args:
            article (dict): article to tokenize

        Returns:
            tokenized_article (list): list of tokenized article parts
        """

        tokenized_article = []

        title, text, popularity_score = (
            article.get("title"),
            article.get("source_text"),
            article.get("popularity_score", 0.0),
        )

        if title.lower().find("(disambiguation)") != -1:
            return None

        if article.get("source_text") is None:
            return None

        title = "unk-title" if title is None else title
        popularity_score = 0.0 if popularity_score is None else popularity_score

        title = normalize_title(title)
        text = clean(text)

        inputs_ids = self.tokenizer.encode(
            f"{title} \n {text}",
            max_length=256,
            stride=64,
            truncation=True,
            add_special_tokens=False,
            return_overflowing_tokens=True,
        )

        for split_id, token_ids in enumerate(inputs_ids):
            tokenized_text = self.tokenizer.decode(token_ids)
            title_id = "-".join(title.split(" "))
            tokenized_rec = {
                "name": f"{title_id}-part-{split_id}",
                "title": title,
                "content": tokenized_text,
                "popularity_score": popularity_score,
            }
            tokenized_article.append(tokenized_rec)

        return tokenized_article

    def tokenize_dump(self, filename: str, output_dir: str = None):
        """
        Tokenize the Cirrus wiki dump

        Args:
            filename (str): name of the file to tokenize

        Returns:
            tokenized_all_docs (list): list of tokenized articles
        """
        doc_tracker, tokenized_doc_tracker = 0, 0

        output_dir = output_dir + "/" if output_dir[-1] != "/" else output_dir
        export_pathfile = (
            output_dir + filename.split("/")[-1].split(".")[0] + "-tokenized.json"
        )
        print(f"Exporting tokenized articles to {export_pathfile}")
        with open(filename, "r", encoding="utf-8") as dump_f:
            for line in tqdm(dump_f, desc="Tokenizing articles"):
                try:
                    doc = json.loads(line)
                    doc = dict(doc)
                except json.decoder.JSONDecodeError:
                    print("JSONDecodeError, skipping line")
                    continue

                if doc.get("source_text") is None:
                    continue

                tokenized_article = self.tokenize_content(doc)

                doc_tracker += 1
                if tokenized_article is None:
                    continue

                tokenized_doc_tracker += len(tokenized_article)

                for article in tokenized_article:
                    try:
                        with open(export_pathfile, "a", encoding="utf-8") as export_f:
                            export_f.write(json.dumps(article) + "\n")
                    except Exception as e:
                        raise (f"Error while writing to {export_pathfile}: {e}")

                if len(doc_tracker) % 1_000_000 == 0:
                    print(f"Tokenized {doc_tracker} articles")

        print(
            f"Processed {doc_tracker} articles, which generated {tokenized_doc_tracker} tokenized articles"
        )
        return export_pathfile

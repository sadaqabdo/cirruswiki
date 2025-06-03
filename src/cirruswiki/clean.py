import html
import re
from html.entities import name2codepoint

# fmt: off
discardElements = [
    'gallery', 'timeline', 'noinclude', 'pre',
    'table', 'tr', 'td', 'th', 'caption', 'div',
    'form', 'input', 'select', 'option', 'textarea',
    'ul', 'li', 'ol', 'dl', 'dt', 'dd', 'menu', 'dir',
    'ref', 'references', 'img', 'imagemap', 'source', 'small'
]
# fmt: off
wgUrlProtocols = [
    'bitcoin:', 'ftp://', 'ftps://', 'geo:', 'git://', 'gopher://', 'http://',
    'https://', 'irc://', 'ircs://', 'magnet:', 'mailto:', 'mms://', 'news:',
    'nntp://', 'redis://', 'sftp://', 'sip:', 'sips:', 'sms:', 'ssh://',
    'svn://', 'tel:', 'telnet://', 'urn:', 'worldwind://', 'xmpp:', '//'
]

# fmt: off
LATIN_MAPPING = {
    'Å': 'A', 'Ä': 'A', 'Á': 'A', 'Â': 'A', 'À': 'A', 'Ã': 'A', 'Æ': 'AE', 'Ç': 'C', 
    'É': 'E', 'Ê': 'E', 'È': 'E', 'Ë': 'E', 'Í': 'I', 'Î': 'I', 'Ì': 'I', 'Ï': 'I',
    'Ñ': 'N', 'Ö': 'O', 'Ó': 'O', 'Ô': 'O', 'Ò': 'O', 'Õ': 'O', 'Ø': 'O', 'Ü': 'U',
    'Ú': 'U', 'Û': 'U', 'Ù': 'U', 'Ÿ': 'Y', 'á': 'a', 'â': 'a', 'à': 'a', 'ã': 'a', 
    'ä': 'a', 'å': 'a', 'æ': 'ae', 'ç': 'c', 'é': 'e', 'ê': 'e', 'è': 'e', 'ë': 'e',
    'í': 'i', 'î': 'i', 'ì': 'i', 'ï': 'i', 'ñ': 'n', 'ö': 'o', 'ó': 'o', 'ô': 'o', 
    'ò': 'o', 'õ': 'o', 'ø': 'o', 'ü': 'u', 'ú': 'u', 'û': 'u', 'ù': 'u', 'ÿ': 'y'
}

acceptedNamespaces = ["w", "wiktionary", "wikt"]

EXT_LINK_URL_CLASS = r'[^][<>"\x00-\x20\x7F\s]'
ExtLinkBracketedRegex = re.compile(
    "(?i)\[(("
    + "|".join(wgUrlProtocols)
    + ")"
    + EXT_LINK_URL_CLASS
    + r"+)\s*([^\]\x00-\x08\x0a-\x1F]*?)\]",
    re.S | re.U,
)
EXT_IMAGE_REGEX = re.compile(
    r"""(?i)^(http://|https://)([^][<>"\x00-\x20\x7F\s]+)
    /([A-Za-z0-9_.,~%\-+&;#*?!=()@\x80-\xFF]+)\.(gif|png|jpg|jpeg)$""",
    re.X | re.S | re.U,
)
tailRE = re.compile(r"\w+")
syntaxhighlight = re.compile(
    "&lt;syntaxhighlight .*?&gt;(.*?)&lt;/syntaxhighlight&gt;", re.DOTALL
)

placeholder_tags = {"math": "formula", "code": "codice"}
placeholder_tag_patterns = [
    (
        re.compile(
            r"<\s*%s(\s*| [^>]+?)>.*?<\s*/\s*%s\s*>" % (tag, tag),
            re.DOTALL | re.IGNORECASE,
        ),
        repl,
    )
    for tag, repl in placeholder_tags.items()
]

# Match preformatted lines
preformatted = re.compile(r"^ .*?$")

# Match external links (space separates second optional parameter)
externalLink = re.compile(r"\[\w+[^ ]*? (.*?)]")
externalLinkNoAnchor = re.compile(r"\[\w+[&\]]*\]")

# Matches bold/italic
bold_italic = re.compile(r"'''''(.*?)'''''")
bold = re.compile(r"'''(.*?)'''")
italic_quote = re.compile(r"''\"([^\"]*?)\"''")
italic = re.compile(r"''(.*?)''")
quote_quote = re.compile(r'""([^"]*?)""')


# Matches space
spaces = re.compile(r" {2,}")

# Matches dots
dots = re.compile(r"\.{4,}")

# Match HTML comments
# The buggy template {{Template:T}} has a comment terminating with just "->"
comment = re.compile(r"<!--.*?-->", re.DOTALL)

# Match selfClosing HTML tags
selfClosingTags = ("br", "hr", "nobr", "ref", "references", "nowiki")
selfClosing_tag_patterns = [
    re.compile(r"<\s*%s\b[^>]*/\s*>" % tag, re.DOTALL | re.IGNORECASE)
    for tag in selfClosingTags
]

# Match ignored tags
ignored_tag_patterns = []


class MagicWords:

    """
    One copy in each Extractor.

    @see https://doc.wikimedia.org/mediawiki-core/master/php/MagicWord_8php_source.html
    """
    
    switches = (
        "__NOTOC__",
        "__FORCETOC__",
        "__TOC__",
        "__TOC__",
        "__NEWSECTIONLINK__",
        "__NONEWSECTIONLINK__",
        "__NOGALLERY__",
        "__HIDDENCAT__",
        "__NOCONTENTCONVERT__",
        "__NOCC__",
        "__NOTITLECONVERT__",
        "__NOTC__",
        "__START__",
        "__END__",
        "__INDEX__",
        "__NOINDEX__",
        "__STATICREDIRECT__",
        "__DISAMBIG__",
    )


magicWordsRE = re.compile("|".join(MagicWords.switches))


def makeExternalLink(url, anchor):
    """Function applied to wikiLinks"""
    return anchor


def makeExternalImage(url, alt=""):
    return alt


def dropSpans(spans, text):
    """
    Drop from text the blocks identified in :param spans:, possibly nested.
    """
    spans.sort()
    res = ""
    offset = 0
    for s, e in spans:
        if offset <= s:  # handle nesting
            if offset < s:
                res += text[offset:s]
            offset = e
    res += text[offset:]
    return res


def dropNested(text, openDelim, closeDelim):
    """
    A matching function for nested expressions, e.g. namespaces and tables.
    """
    openRE = re.compile(openDelim, re.IGNORECASE)
    closeRE = re.compile(closeDelim, re.IGNORECASE)
    # partition text in separate blocks { } { }
    spans = []  # pairs (s, e) for each partition
    nest = 0  # nesting level
    start = openRE.search(text, 0)
    if not start:
        return text
    end = closeRE.search(text, start.end())
    next = start
    while end:
        next = openRE.search(text, next.end())
        if not next:  # termination
            while nest:  # close all pending
                nest -= 1
                end0 = closeRE.search(text, end.end())
                if end0:
                    end = end0
                else:
                    break
            spans.append((start.start(), end.end()))
            break
        while end.end() < next.start():
            # { } {
            if nest:
                nest -= 1
                # try closing more
                last = end.end()
                end = closeRE.search(text, end.end())
                if not end:  # unbalanced
                    if spans:
                        span = (spans[0][0], last)
                    else:
                        span = (start.start(), last)
                    spans = [span]
                    break
            else:
                spans.append((start.start(), end.end()))
                # advance start, find next close
                start = next
                end = closeRE.search(text, next.end())
                break  # { }
        if next != start:
            # { { }
            nest += 1
    # collect text outside partitions
    return dropSpans(spans, text)


def replaceExternalLinks(text):
    s = ""
    cur = 0
    for m in ExtLinkBracketedRegex.finditer(text):
        s += text[cur : m.start()]
        cur = m.end()

        url = m.group(1)
        label = m.group(3)

        # # The characters '<' and '>' (which were escaped by
        # # removeHTMLtags()) should not be included in
        # # URLs, per RFC 2396.
        # m2 = re.search('&(lt|gt);', url)
        # if m2:
        #     link = url[m2.end():] + ' ' + link
        #     url = url[0:m2.end()]

        # If the link text is an image URL, replace it with an <img> tag
        # This happened by accident in the original parser, but some people used it extensively
        m = EXT_IMAGE_REGEX.match(label)
        if m:
            label = makeExternalImage(label)

        # Use the encoded URL
        # This means that users can paste URLs directly into the text
        # Funny characters like ö aren't valid in URLs anyway
        # This was changed in August 2004
        s += makeExternalLink(url, label)  # + trail

    return s + text[cur:]


def replaceInternalLinks(text):
    """
    Replaces external links of the form:
    [[title |...|label]]trail

    with title concatenated with trail, when present, e.g. 's' for plural.
    """
    # call this after removal of external links, so we need not worry about
    # triple closing ]]].
    cur = 0
    res = ""
    for s, e in findBalanced(text, ["[["], ["]]"]):
        m = tailRE.match(text, e)
        if m:
            trail = m.group(0)
            end = m.end()
        else:
            trail = ""
            end = e
        inner = text[s + 2 : e - 2]
        # find first |
        pipe = inner.find("|")
        if pipe < 0:
            title = inner
            label = title
        else:
            title = inner[:pipe].rstrip()
            # find last |
            curp = pipe + 1
            for s1, e1 in findBalanced(inner, ["[["], ["]]"]):
                last = inner.rfind("|", curp, s1)
                if last >= 0:
                    pipe = last  # advance
                curp = e1
            label = inner[pipe + 1 :].strip()
        res += text[cur:s] + makeInternalLink(title, label) + trail
        cur = end
    return res + text[cur:]


def findBalanced(text, openDelim, closeDelim):
    """
    Assuming that text contains a properly balanced expression using
    :param openDelim: as opening delimiters and
    :param closeDelim: as closing delimiters.
    :return: an iterator producing pairs (start, end) of start and end
    positions in text containing a balanced expression.
    """
    openPat = "|".join([re.escape(x) for x in openDelim])
    # patter for delimiters expected after each opening delimiter
    afterPat = {
        o: re.compile(openPat + "|" + c, re.DOTALL)
        for o, c in zip(openDelim, closeDelim)
    }
    stack = []
    start = 0
    cur = 0
    # end = len(text)
    startSet = False
    startPat = re.compile(openPat)
    nextPat = startPat
    while True:
        next = nextPat.search(text, cur)
        if not next:
            return
        if not startSet:
            start = next.start()
            startSet = True
        delim = next.group(0)
        if delim in openDelim:
            stack.append(delim)
            nextPat = afterPat[delim]
        else:
            stack.pop()
            # assert opening == openDelim[closeDelim.index(next.group(0))]
            if stack:
                nextPat = afterPat[stack[-1]]
            else:
                yield start, next.end()
                nextPat = startPat
                start = next.end()
                startSet = False
        cur = next.end()


def makeInternalLink(title, label):
    colon = title.find(":")
    if colon > 0 and title[:colon] not in acceptedNamespaces:
        return ""
    if colon == 0:
        # drop also :File:
        colon2 = title.find(":", colon + 1)
        if colon2 > 1 and title[colon + 1 : colon2] not in acceptedNamespaces:
            return ""

    return label


def unescape(text):
    """
    Removes HTML or XML character references and entities from a text string.

    :param text The HTML (or XML) source text.
    :return The plain text, as a Unicode string, if necessary.
    """

    def fixup(m):
        text = m.group(0)
        code = m.group(1)
        try:
            if text[1] == "#":  # character reference
                if text[2] == "x":
                    return chr(int(code[1:], 16))
                else:
                    return chr(int(code))
            else:  # named entity
                return chr(name2codepoint[code])
        except:
            return text  # leave as is

    return re.sub("&#?(\w+);", fixup, text)


def latinize(input_str):
    """
    Converts a string to ASCII by replacing non-ASCII characters with their closest ASCII equivalents.
    :param input_str: the string to convert.
    :return: the converted string.
    """
    return "".join([LATIN_MAPPING.get(c, c) for c in input_str])


def clean(text, expand_templates=False, html_safe=True):
    """
    Transforms wiki markup. If the command line flag --escapedoc is set then the text is also escaped
    @see https://www.mediawiki.org/wiki/Help:Formatting
    :param extractor: the Extractor t use.
    :param text: the text to clean.
    :param expand_templates: whether to perform template expansion.
    :param html_safe: whether to convert reserved HTML characters to entities.
    @return: the cleaned text.
    """
    text = re.sub(r"\[\[Category:(.*?)\]\]", r"\1", text)

    text = dropNested(text, r"{{", r"}}")

    # Drop tables
    text = dropNested(text, r"{\|", r"\|}")

    # replace external links
    text = replaceExternalLinks(text)

    # replace internal links
    text = replaceInternalLinks(text)

    # drop MagicWords behavioral switches
    text = magicWordsRE.sub("", text)

    # ############### Process HTML ###############

    # turn into HTML, except for the content of <syntaxhighlight>
    res = ""
    cur = 0
    for m in syntaxhighlight.finditer(text):
        end = m.end()
        res += unescape(text[cur : m.start()]) + m.group(1)
        cur = end
    text = res + unescape(text[cur:])

    # Handle bold/italic/quote
    text = bold_italic.sub(r"\1", text)
    text = bold.sub(r"\1", text)
    text = italic_quote.sub(r'"\1"', text)
    text = italic.sub(r'"\1"', text)
    text = quote_quote.sub(r'"\1"', text)
    # residuals of unbalanced quotes
    text = text.replace("'''", "").replace("''", '"')

    # Collect spans

    spans = []
    # Drop HTML comments
    for m in comment.finditer(text):
        spans.append((m.start(), m.end()))

    # Drop self-closing tags
    for pattern in selfClosing_tag_patterns:
        for m in pattern.finditer(text):
            spans.append((m.start(), m.end()))

    # Drop ignored tags
    for left, right in ignored_tag_patterns:
        for m in left.finditer(text):
            spans.append((m.start(), m.end()))
        for m in right.finditer(text):
            spans.append((m.start(), m.end()))

    # Bulk remove all spans
    text = dropSpans(spans, text)

    # Drop discarded elements
    for tag in discardElements:
        text = dropNested(text, r"<\s*%s\b[^>/]*>" % tag, r"<\s*/\s*%s>" % tag)

    text = unescape(text)

    # Expand placeholders
    for pattern, placeholder in placeholder_tag_patterns:
        index = 1
        for match in pattern.finditer(text):
            text = text.replace(match.group(), "%s_%d" % (placeholder, index))
            index += 1

    text = text.replace("<<", "«").replace(">>", "»")

    #############################################

    # Cleanup text
    text = text.replace("\t", " ")
    text = re.sub(r"\s*=+\s*([^=]*)\s*=+\s*", "\n", text)
    text = spaces.sub(" ", text)
    text = dots.sub("...", text)
    text = re.sub(" (,:\.\)\]»)", r"\1", text)
    text = re.sub("(\[\(«) ", r"\1", text)
    text = re.sub(r"\(\s*[^\w\s]*\s*\)", "", text)
    text = re.sub(r"\n\W+?\n", "\n", text, flags=re.U)  # lines with only punctuations
    text = text.replace(",,", ",").replace(",.", ".")
    text = re.sub(r"\*\s*[^\w\s].*\n|\*\s*\n", "", text)
    if not html_safe:
        text = html.escape(text, quote=False)
    text = text.split("\n")
    text = "\n".join([line.strip() for line in text if line.strip()])
    text = latinize(text)
    return text


def ucfirst(string):
    """:return: a string with just its first character uppercase
    We can't use title() since it coverts all words.
    """
    if string:
        if len(string) > 1:
            return string[0].upper() + string[1:]
        else:
            return string.upper()
    else:
        return ""


def normalizeNamespace(ns):
    return ucfirst(ns)


def normalize_title(title):
    """Normalize title"""
    # remove leading/trailing whitespace and underscores
    title = latinize(title)
    title = title.strip(" _")
    # replace sequences of whitespace and underscore chars with a single space
    title = re.sub(r"[\s_]+", " ", title)
    title = ucfirst(title)
    return title

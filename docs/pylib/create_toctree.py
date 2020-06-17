"""
Build a TOC-tree; Sphinx requires it and this makes it easy to just
add/build/link new files without needing to explicitly add it to a toctree
directive somewhere.

"""

import re
from sphinx.errors import DocumentError
from pathlib import Path
from os.path import abspath, dirname, join as pathjoin, sep

_IGNORE_FILES = []
_SOURCE_DIR = pathjoin(dirname(dirname(abspath(__file__))), "source")
_TOC_FILE = pathjoin(_SOURCE_DIR, "toc.md")


def create_toctree():
    """
    Create source/toc.md file
    """

    docref_map = {}

    for path in Path(_SOURCE_DIR).rglob("*.md"):
        # find the source/ part of the path and strip it out
        # support nesting of 3 within source/ dir
        fname = path.name
        if fname in _IGNORE_FILES:
            # this is the name including .md
            continue
        ind = path.parts[-4:].index("source")
        pathparts = path.parts[-4 + 1 + ind:]
        url = "/".join(pathparts)
        url = url.rsplit(".", 1)[0]
        fname = fname.rsplit(".", 1)[0]
        if fname in docref_map:
            raise DocumentError(
                f" Tried to add '{url}.md' when '{docref_map[fname]}.md' already exists.\n"
                " Evennia's auto-link-corrector does not accept doc-files with the same \n"
                " name, even in different folders. Rename one.\n")
        docref_map[fname] = url

    # normal reference-links [txt](urls)
    ref_regex = re.compile(r"\[(?P<txt>[\w -\[\]]+?)\]\((?P<url>.+?)\)", re.I + re.S + re.U)
    # in document references
    ref_doc_regex = re.compile(r"\[(?P<txt>[\w -]+?)\]:\s+?(?P<url>.+?)(?=$|\n)", re.I + re.S + re.U)

    def _sub(match):
        grpdict = match.groupdict()
        txt, url = grpdict['txt'], grpdict['url']

        if "http" in url and "://" in url:
            urlout = url
        else:
            fname, *part = url.rsplit("/", 1)
            fname = part[0] if part else fname
            fname = fname.rsplit(".", 1)[0]
            fname, *anchor = fname.rsplit("#", 1)
            if fname in docref_map:
                urlout = docref_map[fname] + ('#' + anchor[0] if anchor else '')
                if urlout != url:
                    print(f"  Remapped link [{txt}]({url}) -> [{txt}]({urlout})")
            else:
                urlout = url
        return f"[{txt}]({urlout})"

    def _sub_doc(match):
        grpdict = match.groupdict()
        txt, url = grpdict['txt'], grpdict['url']

        if "http" in url and "://" in url:
            urlout = url
        else:
            fname, *part = url.rsplit("/", 1)
            fname = part[0] if part else fname
            fname = fname.rsplit(".", 1)[0]
            fname, *anchor = fname.rsplit("#", 1)
            if fname in docref_map:
                urlout = docref_map[fname] + ('#' + anchor[0] if anchor else '')
                if urlout != url:
                    print(f"  Remapped link [{txt}]: {url} -> [{txt}]: {urlout}")
            else:
                urlout = url
        return f"[{txt}]: {urlout}"

    # replace / correct links in all files
    count = 0
    for path in Path(_SOURCE_DIR).rglob("*.md"):
        with open(path, 'r') as fil:
            intxt = fil.read()
            outtxt = ref_regex.sub(_sub, intxt)
            outtxt = ref_doc_regex.sub(_sub_doc, outtxt)
        if intxt != outtxt:
            with open(path, 'w') as fil:
                fil.write(outtxt)
            count += 1
            print(f"Auto-relinked links in {path.name}")

    if count > 0:
        print(f"Auto-corrected links in {count} documents.")

    # write tocfile
    with open(_TOC_FILE, "w") as fil:
        fil.write("# Toc\n")

        for ref in sorted(docref_map.values()):

            if ref == "toc":
                continue

            linkname = ref.replace("-", " ")
            fil.write(f"\n- [{linkname}]({ref})")

        # we add a self-reference so the toc itself is also a part of a toctree
        fil.write("\n\n```toctree::\n  :hidden:\n\n  toc\n```")

if __name__ == "__main__":
    create_toctree()

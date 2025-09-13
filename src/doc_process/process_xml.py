
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape
from lxml import etree
import os
import copy
from src.logging_config import setup_logger
from src.doc_process.process_doc import chunk_sentences

logger = setup_logger(__name__)

def create_dtbook_xml(
    sections: list[dict],
    output_path: str,
    title: str,
    author: str,
    publisher: str = "Unknown",
    lang: str = "vi",
    uid: str = "bookid-001",
    date = datetime.now().strftime("%Y-%m-%d"),
    split_by_sentence: bool = True,
    chunk_size: int = 400,
):
    """
    Description: Create a strict DAISY 3-compliant DTBook XML file.
    Input:
        sections: list[dict], List of dicts with {"title": str, "content": str}.
        output_path: str, File path to save the DTBook.
        title: str, Book title.
        author: str, Book author.
        publisher: str, Publisher (default: "Unknown").
        lang: str, Language code (default: "vi").
        uid: str, Unique identifier for the book.
        date: str, Date of the book.
        split_by_sentence: bool, Whether to split content into sentences (default: True).
        chunk_size: int, Number of words per chunk if splitting (default: 200) only work if split_by_sentence is False.
    Return:
        output_path: str, File path to the saved DTBook.
    """

    # Header
    dtbook_header = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE dtbook PUBLIC "-//NISO//DTD dtbook 2005-3//EN"
    "http://www.daisy.org/z3986/2005/dtbook-2005-3.dtd">
<dtbook version="2005-3" xml:lang="{lang}" xmlns="http://www.daisy.org/z3986/2005/dtbook/">
  <head>
    <meta name="dc:Title" content="{escape(title)}"/>
    <meta name="dc:Creator" content="{escape(author)}"/>
    <meta name="dc:Publisher" content="{escape(publisher)}"/>
    <meta name="dc:Language" content="{escape(lang)}"/>
    <meta name="dc:Date" content="{escape(date)}"/>
    <meta name="dc:Format" content="ANSI/NISO Z39.86-2005"/>
    <meta name="dc:Identifier" content="{escape(uid)}"/>
  </head>
  <book>
    <frontmatter>
      <doctitle>{escape(title)}</doctitle>
      <docauthor>{escape(author)}</docauthor>
    </frontmatter>
    <bodymatter>
'''

    # Body sections
    body_content = ""
    for idx, sec in enumerate(sections, 0):
        body_content += f'      <level1 class="chapter">\n'
        body_content += f'        <pagenum>{sec["page"]}</pagenum>\n'
        body_content += f'        <h1><sent id="c{idx}_title" data-pid="c{idx}_title">{escape(sec["title"])}</sent></h1>\n'
        body_content += f'          <p>\n'
        # Split line by line breaks
        if split_by_sentence:
            for line_id, line in enumerate(sec["content"].split("\n")):
                line = line.strip()
                if line:
                    body_content += f'        <sent data-pid="c{idx}_c{line_id}" id="c{idx}_c{line_id}">{escape(line)}</sent>\n'
        else:
            chunks = chunk_sentences(sec["content"], chunk_size)
            for chunk_id, chunk in enumerate(chunks):
                chunk = chunk.strip()
                if chunk:
                    body_content += f'        <sent data-pid="c{idx}_c{chunk_id}" id="c{idx}_c{chunk_id}">{escape(chunk)}</sent>\n'
        
        
        body_content += f'          </p>\n'
        body_content += f'      </level1>\n'

    # Footer
    dtbook_footer = """    </bodymatter>
    <rearmatter></rearmatter>
  </book>
</dtbook>
"""

    # Save file
    Path(output_path).write_text(dtbook_header + body_content + dtbook_footer, encoding="utf-8")
    logger.info(f"✅ Strict DTBook saved at: {output_path}")
    return output_path


def split_dtbook_by_chapter(input_file: str, output_dir: str):
    """
    Description: Split a DTBook XML into per-chapter files.
    Input:
        input_file: str, the path to the input DTBook XML file.
        output_dir: str, the directory to save the output chapter files.
    Return:
        chapters_output_lst: list, a list of paths to the output chapter files.
    """
    
    chapters_output_lst = []

    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(input_file, parser)
    root = tree.getroot()

    # Detect namespace
    if root.tag.startswith("{"):
        NS = root.tag.split("}")[0].strip("{")
        nsmap = {None: NS}
        ns_prefix = f"{{{NS}}}"
    else:
        NS = None
        nsmap = None
        ns_prefix = ""

    bodymatter = root.find(f".//{ns_prefix}bodymatter")
    if bodymatter is None:
        raise ValueError("No <bodymatter> found in the DTBook XML")

    chapters = bodymatter.findall(f"{ns_prefix}level1")
    if not chapters:
        raise ValueError("No <level1> chapters found in the DTBook XML")

    for idx, chapter in enumerate(chapters):
        chapter_copy = copy.deepcopy(chapter)

        # New <dtbook>
        new_root = etree.Element("dtbook", nsmap=nsmap)
        new_root.attrib.update(root.attrib)

        # Copy <head>
        head = root.find(f"{ns_prefix}head")
        if head is not None:
            new_root.append(copy.deepcopy(head))

        # Create <book>
        book_elem = etree.Element("book", nsmap=nsmap)

        # Copy <frontmatter> (with content)
        front = root.find(f".//{ns_prefix}frontmatter")
        book_elem.append(copy.deepcopy(front) if front is not None else etree.Element("frontmatter", nsmap=nsmap))

        # New <bodymatter> with one chapter
        new_body = etree.Element("bodymatter", nsmap=nsmap)
        new_body.append(chapter_copy)
        book_elem.append(new_body)

        # Copy <rearmatter>
        rear = root.find(f"{ns_prefix}rearmatter")
        book_elem.append(copy.deepcopy(rear) if rear is not None else etree.Element("rearmatter", nsmap=nsmap))

        # Attach <book> to root
        new_root.append(book_elem)

        # Save file
        out_file = os.path.join(output_dir, f"chapter_{idx}.dtbook.xml")
        etree.ElementTree(new_root).write(
            out_file,
            pretty_print=True,
            encoding="utf-8",
            xml_declaration=True,
            doctype='<!DOCTYPE dtbook PUBLIC "-//NISO//DTD dtbook 2005-3//EN"\n    "http://www.daisy.org/z3986/2005/dtbook-2005-3.dtd">'
        )
        logger.info(f"✅ Saved {out_file}")
        chapters_output_lst.append(out_file)
    return chapters_output_lst
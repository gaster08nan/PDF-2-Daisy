
import re
import pymupdf


def split_sentences_with_newline(text: str) -> str:
    """
    Description: Insert a newline after each sentence-ending punctuation, but ignore numerical lists like '1.', '2.', or 'Chương 1.'.
    Input:
        text: str, The input text.
    Return:
        str: Text with '\n' at the end of each sentence.
    """
    # First, protect list markers by replacing "N." with a placeholder
    protected = re.sub(
        r"(?i)\b(chương\s+\d+|\d+)\.",  # match "1." or "Chương 1."
        lambda m: m.group(0).replace(".", "<DOT>"),
        text,
    )

    # Add newline after sentence-ending punctuation (., ?, !, ...)
    protected = re.sub(r"(\.\.\.|[.!?])", r"\1\n", protected)

    # Restore protected list markers
    normalized = protected.replace("<DOT>", ".")
    normalized = normalized.replace("“", '"').replace("”", '"')
    normalized = normalized.replace("...", ".\n")  # Ensure ellipses also get a newline

    # Clean up extra newlines
    return re.sub(r"\n+", "\n", normalized).strip()

def chunk_sentences(texts: list[str], max_len: int = 200) -> list[str]:
    """
    Description: Spilt the full chapter text into chunks with max length of max_len.
    Input:
        texts: str, The input text.
    Return:
        str: Text with '\n' at the end of each sentence with the length of max_len.
    """
    chunks, current = [], ""

    for sentence in texts.split("\n"):
        if len(current) + len(sentence) + 1 <= max_len:
            current += (" " if current else "") + sentence
        else:
            if current:
                chunks.append(current.strip())
            current = sentence
    if current:
        chunks.append(current.strip())
    return chunks

def process_pdf(pdf_file):
    """
    Description: Process a pdf file and return a list of sections.
    Input:
        pdf_file: str, the path to the pdf file.
    Return:
        section_list: list, a list of sections, each section is a dictionary with title, page and content.
    """
    doc = pymupdf.open(pdf_file)

    _, last_chapter_name, last_chapter_page = doc.get_toc()[0]
    section_list = []
    chapter_content = ""
    for idx, toc_items in enumerate(doc.get_toc()[1:]):
        _, current_chapter_name, current_page = toc_items
        chapter_content = ""
        for page in doc.pages(int(last_chapter_page)-1, int(current_page)):
            chapter_content += page.get_text()

        chapter_content = chapter_content.replace("\n", " ")
        if len(last_chapter_name.split(" ")) == 1:
            chapter_content = chapter_content.split(current_chapter_name)[0]
            chapter_content = f"{last_chapter_name} ".join(chapter_content.split(last_chapter_name)[1:])
        else:
            chapter_content = chapter_content.split(last_chapter_name)[-1].split(current_chapter_name)[0]
            chapter_content = split_sentences_with_newline(chapter_content)


        section_list.append(
            {"title": last_chapter_name, 
                "page": last_chapter_page, 
                "content": chapter_content.strip()}
        )
        # if idx == 11:
        #     breakpoint()
        last_chapter_name = current_chapter_name
        last_chapter_page = current_page

    # add last chapter content
    for page in doc.pages(int(current_page)-1, len(doc)):
        chapter_content += page.get_text()
    chapter_content = chapter_content.replace("\n", " ")
    chapter_content = chapter_content.split(current_chapter_name)[-1]
    chapter_content = split_sentences_with_newline(chapter_content)

    section_list.append(
                    {"title": current_chapter_name, 
                        "page": current_page, 
                        "content": chapter_content.strip()}
                )

    doc.close()
    return section_list


def cut_pdf_by_chapter(pdf_file: str, chapter_title: str, output_pdf: str):
    """
    Description: Create a new pdf file from the begining until the input chapter name. Cut off the text after the chapter name by drawing a white rectangle over it.
    Input:
        pdf_file: str, the path to the pdf file.
        chapter_title: str, the chapter name to cut the pdf.
        output_pdf: str, the path to save the new pdf file.
    Return:
        output_pdf: str, the path to the new pdf file.
    """
    doc = pymupdf.open(pdf_file)
    new_doc = pymupdf.open()
    
    toc = doc.get_toc()

    # Filter: keep only titles until the given chapter_title
    filtered_toc = []
    i = 0
    while True:
        idx, title, page = toc[i]
        filtered_toc.append([idx, title, page])
        if chapter_title in title:
            filtered_toc.append(toc[i + 1])
            break
        i += 1
    
    _, _, page_start = filtered_toc[0]
    _, last_title, page_end = filtered_toc[-1]

    # Copy relevant pages
    new_doc.insert_pdf(doc, from_page=page_start, to_page=page_end - 1)
    last_page = new_doc[-1]  # last page of new doc

    # Extract full text
    full_text = last_page.get_text("text")
    new_text = full_text.split(last_title)[0].strip()

    if new_text:  # only mask if something remains above cutoff
        # Locate the block containing the cutoff title
        blocks = last_page.get_text("blocks")
        block_found = None
        for block in blocks:
            if last_title in block[4]:  # block[4] is text content
                block_found = block
                break

        if block_found:
            # b = (x0, y0, x1, y1, "text", block_no, block_type, ...)
            _, y0, _, _, _, _, _ = block_found
            page_rect = last_page.rect
            erase_rect = pymupdf.Rect(0, y0, page_rect.width, page_rect.height)

            # Draw white rectangle to mask unwanted text
            last_page.draw_rect(erase_rect, color=(1, 1, 1), fill=(1, 1, 1))

    # Update TOC (exclude the extra appended one)
    new_doc.set_toc(filtered_toc[:-1])

    # Save
    new_doc.save(output_pdf)
    new_doc.close()
    doc.close()

    return output_pdf
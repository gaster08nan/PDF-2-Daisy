from src.doc_process.process_doc import process_pdf, chunk_sentences
from src.doc_process.process_xml import create_dtbook_xml, split_dtbook_by_chapter
from datetime import datetime
import os
from src.logging_config import setup_logger
logger = setup_logger(__name__)

class TextProcessor:
    
    def __init__(self, input_file=None, output_dir=None, split_by_sentence=False, chunk_size=200):
        """
        Description: Initialize the TextProcessor class.
        Input:
            input_file: str, the path to the input pdf file.
            output_dir: str, the directory to save the output files.
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.split_by_sentence = split_by_sentence
        self.chunk_size = chunk_size
        self.processed_lst = []
        
        if self.output_dir is not None and not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def make_xml_lst(self, title = "book title", 
                author = "author name", 
                date = datetime.now().strftime("%Y-%m-%d"), 
                publisher = "Unknown", 
                uid = "000-xxx-xxx-000",
                ):
        """
        Description: Create a list of xml chapters from a pdf file, split by sentence.
        Input:
            title: str, the title of the book.
            author: str, the author of the book.
            date: str, the date of the book.
            publisher: str, the publisher of the book.
            uid: str, the uid of the book.
        Return:
            xml_chapters_lst: list, a list of xml chapters.
        """
        if self.input_file.lower().endswith('.pdf'):
            self.processed_lst = process_pdf(self.input_file)
            output_file = title.replace(".pdf",".xml")
            dtbook_xml = create_dtbook_xml(self.processed_lst, output_path=f"{self.output_dir}/{output_file}",
                                title=title,
                                author= author,
                                date=date,
                                publisher=publisher,
                                uid=uid,
                                split_by_sentence=self.split_by_sentence,
                                chunk_size=self.chunk_size)
            xml_chapters_lst = split_dtbook_by_chapter(dtbook_xml, self.output_dir)
            return xml_chapters_lst
        else:
            logger.error("Unsupported file format. Only PDF and XML are supported.")
            raise ValueError("Unsupported file format. Only PDF and XML are supported.")
    
    def create_tsv_for_tts(self, promt_wav_file, prompt_text, output_dir='tsv_dir/'):
        """
        Description: Create tsv files for TTS split with each line.
        Input:
            section_lst: list, a list of chapters.
            promt_wav_file: str, the path to the prompt wav file.
            prompt_text: str, the prompt text.
            output_dir: str, the directory to save the tsv files.
        """
        for i, chapter in enumerate(self.processed_lst[:]):
            chapter_name = f"chapter_{i}"
            if not os.path.exists(f"{output_dir}/{chapter_name}"):
                os.makedirs(f"{output_dir}/{chapter_name}")
                
            lines = chapter.get('title')+"\n"+chapter.get('content')
            lines = lines.split('\n')
            short_line = ""
            for j, line in enumerate(lines):
                if line.strip() in [".", "(", ")", "<", ">", "", ";", "'", '"', ]:
                    continue
                    
                if len(line.strip()) < 10:
                    short_line += " " + line.strip()
                    continue
                else:
                    
                    if short_line != "":
                        line = short_line+" "+ line.strip()
                        short_line = ""

                    with open(f"{output_dir}/{chapter_name}/chapter_{i}.tsv", "a", encoding="utf-8") as f:
                        f.write(f"{chapter_name}_{j}\t{prompt_text}\t{promt_wav_file}\t{line.strip()}\n")
            
            if short_line != "":
                with open(f"{output_dir}/{chapter_name}/chapter_{i}.tsv", "a", encoding="utf-8") as f:
                        f.write(f"{chapter_name}_{j}\t{prompt_text}\t{promt_wav_file}\t{short_line.strip()}\n")

            f.close()
            logger.info(f"List of tsv created successfully. Total {j} files for chapter {i}")
            
    def create_tts_for_tts_with_chunks(self, promt_wav_file, prompt_text, output_dir='tsv_dir/'):
        """
        Description: Create tsv files for TTS split by chunk.
        Input:
            section_lst: list, a list of chapters.
            promt_wav_file: str, the path to the prompt wav file.
            prompt_text: str, the prompt text.
            output_dir: str, the directory to save the tsv files.
        """
        for i, chapter in enumerate(self.processed_lst[:]): 
            chapter_name = f"chapter_{i}"
            if not os.path.exists(f"{output_dir}/{chapter_name}"):
                os.makedirs(f"{output_dir}/{chapter_name}")
                
            lines = chapter.get('title')+"\n"+chapter.get('content')
            chunks = chunk_sentences(lines, max_len=self.chunk_size)
            for j, chunk in enumerate(chunks):
                with open(f"{output_dir}/{chapter_name}/chapter_{i}.tsv", "a", encoding="utf-8") as f:
                    f.write(f"{chapter_name}_{j}\t{prompt_text}\t{promt_wav_file}\t{chunk.strip()}\n")
            f.close()
            logger.info(f"List of tsv created successfully. Total {j} files for chapter {i}")
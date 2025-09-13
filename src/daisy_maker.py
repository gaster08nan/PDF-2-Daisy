from src.audio_process.audio_processor import AudioProcessor
from src.doc_process.text_processor import TextProcessor
from src.logging_config import setup_logger
from src.utils import read_txt_file
import os 
import glob
import sys
from datetime import datetime
import shutil
from anemone import anemone as anemone_main

logger = setup_logger(__name__)



class DaisyMaker:
    def __init__(self, 
                daisy_output_dir,
                audio_output_dir,
                xml_output_dir="xml_output",
                wav_file_path = "src/model/prompt.wav",
                wav_text_path = "src/model/prompt.txt",
                tts_model_dir="src/model",
                tts_checkpoint_dir="iter-525000-avg-2.pt",
                is_split_by_sentence=False,
                chunk_size=400):
        """
        Description: Initialize the DaisyMaker class.
        Input:
            daisy_output_dir: str, the directory to save the daisy book.
            audio_output_dir: str, the directory to save the audio files.
            tts_checkpoint_dir: str, the path to the TTS model checkpoint.
        """
        self.daisy_output_dir = daisy_output_dir
        self.audio_output_dir = audio_output_dir
        self.xml_output_dir = xml_output_dir
        self.tts_checkpoint_dir = tts_checkpoint_dir
        self.tts_model_dir = tts_model_dir
        self.is_split_by_sentence = is_split_by_sentence
        self.chunk_size = chunk_size
        self.audio_processor = AudioProcessor(self.audio_output_dir, wav_file_path=wav_file_path, wav_text_path=wav_text_path, model_dir=self.tts_model_dir, checkpoint_dir=self.tts_checkpoint_dir)
        self.text_processor = TextProcessor(None, self.xml_output_dir, split_by_sentence=self.is_split_by_sentence, chunk_size=self.chunk_size)
        
        os.makedirs(self.daisy_output_dir, exist_ok=True)
        os.makedirs(self.audio_output_dir, exist_ok=True)

    def create_daisy_for_book(self, status_dict, job_id, input_file,
                            book_title="book title",
                            book_author="author name",
                            book_date="2023-01-01",
                            book_publisher="Unknown",
                            book_uid="000-xxx-xxx-000",
                            *args, **kwargs):
        """
        Description: Create a daisy book from a pdf file.
        Input:
            status_dict: dict, a dictionary to store the status of the job.
            job_id: str, the id of the job.
            input_file: str, the path to the pdf file.
            book_title: str, the title of the book.
            book_author: str, the author of the book.
            book_date: str, the date of the book.
            book_publisher: str, the publisher of the book.
            book_uid: str, the uid of the book.
        """
        try:
            self.text_processor = TextProcessor(input_file, self.xml_output_dir)
            book_date = datetime.strptime(book_date, "%m/%d/%Y").strftime("%Y-%m-%d")

            # Step 1: Read pdf and convert to XML format for each chapter
            status_dict["status"] = "Creating XML from PDF..."
            xml_chapters_lst = self.text_processor.make_xml_lst(title=book_title,
                                                           author=book_author,
                                                           date=book_date,
                                                           publisher=book_publisher,
                                                           uid=book_uid)
            status_dict["progress"] = 10 # Arbitrary progress update

            # Step 2: Create tsv files for TTS
            status_dict["status"] = "Creating TSV files for TTS..."
            prompt_text = read_txt_file("src/model/prompt.txt")[0]
            tsv_path = os.path.join("data", f"tsv_dir_{job_id}")
            
            # Clean up old tsv_dir if it exists to ensure a fresh start
            if os.path.exists(tsv_path):
                shutil.rmtree(tsv_path)

            self.text_processor.create_tts_for_tts_with_chunks(
                                                promt_wav_file="src/model/prompt.wav",
                                                prompt_text=prompt_text,
                                                output_dir=tsv_path,
                                                )
            status_dict["progress"] = 20

            # Step 3: Create audio from TSV files
            status_dict["status"] = "Starting Text-to-Speech synthesis..."
            tsv_lst = sorted(glob.glob(f"{tsv_path}/chapter_*/"), key=lambda x: int(os.path.basename(os.path.normpath(x)).split("_")[-1]))
            
            # This is the longest step, so we pass the status dict to it
            sync_json_lst, merge_audio_lst = self.audio_processor.create_audio_for_book(
                tsv_chapter_list=tsv_lst,
                status_dict=status_dict
            )

            if len(sync_json_lst) != len(xml_chapters_lst) or len(merge_audio_lst) != len(xml_chapters_lst):
                raise ValueError("The number of sync json files, audio files and xml files are not equal.")

            # Step 4: Create daisy book using Anemone-Daisy-Maker
            status_dict["status"] = "Packaging DAISY book..."
            status_dict["progress"] = 95
            
            sys.argv = [
                "anemone",
                "--title", book_title,
                "--creator", book_author,
                "--lang", "vi",
                "--date", book_date,
                "--publisher", book_publisher,
                "--daisy3",
            ]
            sys.argv.extend(merge_audio_lst)
            sys.argv.extend(xml_chapters_lst)
            sys.argv.extend(sync_json_lst)

            logger.info("Running Anemone: %s", " ".join(sys.argv))
            anemone_main()

            # Move output daisy book to the correct directory
            output_zip = "output_daisy.zip"
            final_zip_path = os.path.join(self.daisy_output_dir, f"{book_title}_daisy.zip")
            shutil.move(output_zip, final_zip_path)

            # Clean up the temporary tsv directory
            shutil.rmtree(tsv_path)
            
            logger.info(f"DAISY book created at {final_zip_path}")
            status_dict["progress"] = 100
            status_dict["status"] = "finished"

        except Exception as e:
            logger.error(f"An error occurred during DAISY creation: {e}", exc_info=True)
            status_dict["status"] = f"error: {str(e)}"

        
        
if __name__ == "__main__":
    pdf_path = "data/nhasachmienphi-luyen-tri-nho.pdf"
    book_title = "Luyện Trí Nhớ"
    book_author = "Phan Văn Hồng Thắng"
    book_date = "01/01/2022"
    book_publisher = "NXB Hồng Đức"
    book_uid = "97860422588213"
    
    daisy_maker = DaisyMaker(daisy_output_dir="data/daisy_output_dir", audio_output_dir=f"data/{book_title}_audio_output_dir", xml_output_dir=f"data/{book_title}_xml_output")
    daisy_maker.create_daisy_for_book(input_file=os.path.abspath(pdf_path),
                                      book_title=book_title,
                                      book_author=book_author,
                                      book_date=book_date,
                                      book_publisher=book_publisher,
                                      book_uid=book_uid)
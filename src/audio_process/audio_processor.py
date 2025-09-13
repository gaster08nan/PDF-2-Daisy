import glob
import gc
import torch
import sys
import os
from pydub import AudioSegment
import json
from tqdm import tqdm
from src.utils import read_txt_file, ms_to_anemone_time
from concurrent.futures import ThreadPoolExecutor, as_completed
# 1. Add ZipVoice repo to path
sys.path.append("src/ZipVoice")  # change if cloned elsewhere

# 2. Import the zipvoice main
from zipvoice.bin import infer_zipvoice
from src.logging_config import setup_logger

logger = setup_logger(__name__)


class AudioProcessor:
    def __init__(self, audio_output_dir, wav_file_path, wav_text_path, model_dir="src/model", checkpoint_dir="iter-525000-avg-2.pt"):
        """
        Description: Initialize the AudioProcessor class.
        Input:
            audio_output_dir: str, the directory to save the audio files.
            checkpoint_dir: str, the path to the TTS model checkpoint.
        """
        self.wav_file = wav_file_path
        self.wav_text = read_txt_file(wav_text_path)[0]
        self.audio_output_dir = audio_output_dir
        self.model_dir = model_dir
        self.checkpoint_dir = checkpoint_dir
        
    
        
    def _tts_book(self, tsv_list, result_dir):
        """
        Description: Synthesize audio from a tsv file.
        Input:
            tsv_list: str, the path to the tsv file.
            result_dir: str, the directory to save the audio files.
            model_dir: str, the directory of the TTS model.
        """
        custom_args = [
            "infer_zipvoice",
            "--model-name", "zipvoice",
            "--model-dir", self.model_dir,
            "--checkpoint-name", self.checkpoint_dir,
            "--tokenizer", "espeak",
            "--lang", "vi",
            "--test-list", tsv_list,
            "--res-dir", result_dir,
            "--seed", "240899"
        ]
        sys.argv = custom_args
        # clear unused memory
        torch.cuda.empty_cache()
        gc.collect()
        # Run
        infer_zipvoice.main()
    
    def _merge_wav_in_chapter(self, audio_files, chapter_idx):
        """
        Description: Merge all wav files in a chapter into a single wav file.
        Input:
            audio_files: list, a list of audio files to merge.
            chapter_idx: int, the index of the chapter.
        Return:
            json_file: str, the path to the json file containing the sync information.
            merge_audio_file: str, the path to the merged audio file.
        """

        pause = AudioSegment.silent(duration=800) # 1000 ms = 1 second pause
        json_sync = {
                        "markers": []
                    }
        audio_sync_lst = [
            {"id": f"c{chapter_idx}_title", "time": "0:00"},
        ]

        combined = AudioSegment.from_wav(audio_files[0]) # audio for the title title

        current_ms = len(combined)  # start after title

        for idx, f in enumerate(audio_files[1:]): # second audio is 1st sentence
            audio = AudioSegment.from_wav(f)

            # save audio and duration to a json to sync with text
            audio_sync_lst.append({"id": f"c{chapter_idx}_c{idx}", "time": ms_to_anemone_time(current_ms)})
            combined += audio
            current_ms += len(audio)

            # Add pause if not last file
            if idx < len(audio_files) - 2:
                combined += pause
                current_ms += len(pause)

        # Save JSON
        json_sync = {"markers": audio_sync_lst}
        output_dir = f"{self.audio_output_dir}/chapter_{chapter_idx}"
        
        with open(f"{output_dir}/sync_{chapter_idx}.json", "w") as f:
            json.dump(json_sync, f, ensure_ascii=False, indent=2)

        # Save audio
        combined.export(f"{output_dir}/full_{chapter_idx}.wav", format="wav")
        logger.info(f"\nFinish Merge audio of {chapter_idx}") 
        return f"{output_dir}/sync_{chapter_idx}.json", f"{output_dir}/full_{chapter_idx}.wav"
        
    def create_audio_for_book(self, tsv_chapter_list="tsv_dir", status_dict=None):
        """
        Create audio for a book from TSV directories.
        TTS (GPU) and merging (CPU) are pipelined to run concurrently.
        """
        total_chapters = len(tsv_chapter_list)
        logger.info(f"Total {total_chapters} chapters to process")

        if status_dict:
            status_dict["total"] = total_chapters
            status_dict["progress"] = 0

        merge_audio_lst = []
        sync_json_lst = []

        os.makedirs(self.audio_output_dir, exist_ok=True)
        # ThreadPoolExecutor for CPU merges
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = []

            for i, tts_dir in enumerate(tqdm(tsv_chapter_list, desc="Processing chapters ...")):
                chapter_id_from_dir = os.path.basename(os.path.normpath(tts_dir)).split("_")[-1]

                if status_dict:
                    status_dict["status"] = f"Running TTS for chapter {chapter_id_from_dir}/{total_chapters}"

                # Run TTS (GPU) for this chapter
                for tts_file in sorted(glob.glob(f"{tts_dir}/*.tsv")):
                    chapter = os.path.basename(tts_file).split(".")[0]
                    chapter_id = int(chapter.split("_")[-1])
                    result_dir = f"{self.audio_output_dir}/{chapter}"

                    os.makedirs(result_dir, exist_ok=True)
                    self._tts_book(tts_file, result_dir)

                logger.info(f"Finished TTS for {chapter}")

                # Submit merge job to CPU thread (async)
                audio_wav_files = sorted(
                    glob.glob(f"{result_dir}/*.wav"),
                    key=lambda x: int(x.split("_")[-1].split(".")[0]),
                )
                futures.append(
                    executor.submit(self._merge_wav_in_chapter, audio_wav_files, chapter_id)
                )

                # ✅ While CPU merges chapter N, GPU moves to chapter N+1

                if status_dict:
                    status_dict["progress"] = i + 1
                    logger.info(f"Updated progress to {status_dict['progress']}/{status_dict['total']}")

            # Collect results (merge outputs)
            for future in as_completed(futures):
                json_file, merge_audio_file = future.result()
                sync_json_lst.append(json_file)
                merge_audio_lst.append(merge_audio_file)

        return sync_json_lst, merge_audio_lst

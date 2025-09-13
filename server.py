import os
import uuid
import shutil
import multiprocessing
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.daisy_maker import DaisyMaker

app = FastAPI()

# --- File and Directory Setup ---
UPLOAD_DIR = Path("data/uploads")
OUTPUT_DIR = Path("data/book_outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# --- Global variables (will be set later) ---
manager = None
jobs = None


class Book(BaseModel):
    input_file: str
    book_title: str
    book_author: str
    book_date: str
    book_publisher: str
    book_uid: str
    chunk_size: int = 400

@app.on_event("startup")
def startup_event():
    global manager, jobs
    manager = multiprocessing.Manager()
    jobs = manager.dict()

def run_daisy_creation(job_id: str, status_dict: dict, book_data: dict):
    """The target function to be run in a background process."""
    try:
        status_dict["status"] = "Initializing..."
        status_dict["progress"] = 0
        status_dict["total"] = 1

        # Define paths
        job_output_dir = OUTPUT_DIR / job_id
        daisy_output_dir = job_output_dir / "daisy_output"
        audio_output_dir = job_output_dir / "audio_output"
        xml_output_dir = job_output_dir / "xml_output"

        daisy_output_dir.mkdir(parents=True, exist_ok=True)
        audio_output_dir.mkdir(parents=True, exist_ok=True)
        xml_output_dir.mkdir(parents=True, exist_ok=True)

        if book_data.get("chunk_size") is None or book_data["chunk_size"] <= 0:
            is_split_by_sentence = True
        else:
            is_split_by_sentence = False
        
        daisy_maker = DaisyMaker(
            daisy_output_dir=str(daisy_output_dir),
            audio_output_dir=str(audio_output_dir),
            xml_output_dir=str(xml_output_dir),
            is_split_by_sentence=is_split_by_sentence,
            chunk_size=book_data.get("chunk_size")
        )

        daisy_maker.create_daisy_for_book(
            status_dict=status_dict,
            job_id=job_id,
            **book_data
        )

        final_zip_path = next(daisy_output_dir.glob("*.zip"), None)
        if not final_zip_path:
            raise FileNotFoundError("Final DAISY zip file not found.")

        status_dict["status"] = "finished"
        status_dict["result_path"] = str(final_zip_path)

    except Exception as e:
        print(f"Error in job {job_id}: {e}")
        status_dict["status"] = f"error: {e}"


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        safe_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {"message": "File uploaded successfully", "file_path": str(file_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {e}")


@app.post("/process")
async def process_book(book: Book):
    if jobs is None:
        raise HTTPException(status_code=500, detail="Job manager not initialized")

    job_id = str(uuid.uuid4())
    input_file_path = Path(book.input_file)
    if not input_file_path.exists():
        raise HTTPException(status_code=404, detail=f"Input file not found: {book.input_file}")

    jobs[job_id] = manager.dict({
        "status": "starting",
        "progress": 0,
        "total": 1,
        "result_path": None
    })

    process = multiprocessing.Process(
        target=run_daisy_creation,
        args=(job_id, jobs[job_id], book.dict())
    )
    process.start()

    return {"message": "Processing started", "job_id": job_id}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    job_status = jobs.get(job_id) if jobs else None
    if job_status is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return dict(job_status)


@app.get("/download/{job_id}")
async def download_result(job_id: str):
    job_status = jobs.get(job_id) if jobs else None
    if job_status is None or job_status.get("status") != "finished":
        raise HTTPException(status_code=404, detail="Job not found or not finished")

    result_path = job_status.get("result_path")
    if not result_path or not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Result file not found.")

    return FileResponse(path=result_path, media_type='application/zip', filename=os.path.basename(result_path))


if __name__ == "__main__":
    import uvicorn

    # Initialize multiprocessing manager here (safe for Windows)
    manager = multiprocessing.Manager()
    jobs = manager.dict()

    uvicorn.run(app, host="0.0.0.0", port=4567, workers=1)

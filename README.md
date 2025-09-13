# 📖 DAISY Book Maker

Welcome to the DAISY Book Maker project! This project provides a powerful tool to convert PDF documents into accessible DAISY books, complete with text and audio.

## ✨ Project Flow

This project seamlessly transforms a PDF file into a complete DAISY book. Here's a breakdown of the magic behind the scenes:

1.  **📄 Text Extraction:** The process begins by extracting the text content from your PDF file.
2.  **↔️ XML Conversion:** The extracted text is then converted into an XML format, structured chapter by chapter.
3.  **🗣️ Text-to-Speech (TTS):** Each chapter's text is synthesized into high-quality audio using our custom TTS model.
4.  **📚 DAISY Book Creation:** Finally, the structured XML and the generated audio files are packaged together to create a fully compliant DAISY book, ready for use with DAISY players.

## 🚀 Getting Started

Getting the project up and running is a breeze. Just follow these simple steps.

### ✅ Prerequisites

Make sure you have Python 3.8 or higher installed on your system.

### 💻 Installation

1.  Clone this repository to your local machine.
2.  Install the required dependencies by running the following command in your terminal:

    ```bash
    pip install -r requirements.txt
    ```

## 🏃‍➡️ Running the Application

The project now includes an easy-to-use web interface built with Streamlit. To get it running, you need to start both the backend server and the frontend UI.

### 1. Start the Backend Server

Open a terminal and run the following command to start the FastAPI server:

```bash
uvicorn server:app --host 0.0.0.0 --port 4567 --reload
```

The server will handle the heavy lifting of processing the PDF and creating the DAISY book.

### 2. Start the Web Interface

Open a **new** terminal and run this command:

```bash
streamlit run app.py
```

This will open the web interface in your browser. From there, you can:

-   Upload your PDF file.
-   Fill in the book's metadata (title, author, etc.).
-   Start the creation process and monitor its progress in real-time.
-   Download the final DAISY book as a ZIP file once it's complete.

## 🐳 Docker

For a more isolated and reproducible environment, you can use the provided Dockerfile to run the application in a container.

### Build the Docker Image

```bash
docker build -t daisy-app .
```

### Run the Docker Container

To run the container with GPU support:

```bash
docker run --gpus all -p 8501:8501 -p 4567:4567 -v ./data:/app/data daisy-app
```

If you don't have a GPU or don't want to use it, you can run the container without the `--gpus all` flag:

```bash
docker run -p 8501:8501 -p 4567:4567 -v ./data:/app/data daisy-app
```

Once the container is running, you can access the web interface at [http://localhost:8501](http://localhost:8501).

---

Happy creating! ✨
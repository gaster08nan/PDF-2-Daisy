#!/bin/bash
uvicorn server:app --host 0.0.0.0 --port 4567 &
streamlit run app.py

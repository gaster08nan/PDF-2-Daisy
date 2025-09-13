---
tags:
  - text-to-speech
  - vietnamese
  - ai-model
  - deep-learning
license: cc-by-nc-sa-4.0
library_name: pytorch
datasets:
  - PhoAudioBook
  - ViVoice
  - UEH
model_name: ZipVoice-Vietnamese-2500h
language: vi
---

# 🛑 Important Note ⚠️  
This model is only intended for **research purposes**.  
**Access requests must be made using an institutional, academic, or corporate email**. Requests from public email providers will be denied. We appreciate your understanding.  

# 🎙️ ZipVoice-Vietnamese-2500h
ZipVoice is a series of fast and high-quality zero-shot TTS models based on flow matching.

Key features:
1. Small and fast: only 123M parameters.

2. High-quality voice cloning: state-of-the-art performance in speaker similarity, intelligibility, and naturalness.

3. Multi-lingual: support Chinese and English.

4. Multi-mode: support both single-speaker and dialogue speech generation.

This checkpoint is a compact fine-tuned version of ZipVoice trained on 2500 hours of Vietnamese speech.  

🔗 For more fine-tuning and inference experiments, visit: https://github.com/k2-fsa/ZipVoice.  

📜 **License:** [CC-BY-NC-SA-4.0](https://spdx.org/licenses/CC-BY-NC-SA-4.0) — Non-commercial research use only.  

---

## 📌 Model Details

- **Dataset:** PhoAudioBook, ViVoice, TeacherDinh-UEH.
- **Total dataset durations:** 2500 hours
- **Data processing Technique:**
  - Remove all music background from audios, using facebook demucs model: https://github.com/facebookresearch/demucs
  - Do not use audio files shorter than 1 second or longer than 30 seconds.
  - Keep the default punctuation marks unchanged.
  - Normalize to lowercase format.
- **Training Configuration:**  
  - **Base Model:** ZipVoice with espeak-ng vi for tokenizer  
  - **GPU:** RTX 3090  
  - **Batch Siz:** Max duration 200  
- **Training Progress:** Stopped at **525,000 steps at epoch 11**  

---

## 🛑 Update Note
Thank you, Teacher Định from the University of Economics Ho Chi Minh City (UEH), for providing me with an additional 50-hours high-quality labeled dataset.

Him contact: https://www.facebook.com/luudinhit93
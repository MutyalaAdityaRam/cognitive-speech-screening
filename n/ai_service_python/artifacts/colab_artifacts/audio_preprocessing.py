# audio_preprocessing.py

import os
import librosa
import numpy as np
import soundfile as sf


def preprocess_audio(input_path, output_path):
    try:
        audio, sr = librosa.load(input_path, sr=16000, mono=True)

        audio, _ = librosa.effects.trim(audio, top_db=20)

        if len(audio) == 0 or np.max(np.abs(audio)) == 0:
            return {
                "status": False,
                "message": "No voice detected. Please restart reading."
            }

        audio = audio / np.max(np.abs(audio))

        sf.write(output_path, audio, 16000)

        return {
            "status": True,
            "message": "Audio processed successfully",
            "processed_path": output_path
        }

    except Exception as e:
        return {
            "status": False,
            "message": f"Processing failed: {str(e)}"
        }


def preprocess_audio_folder(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    success = 0
    failed = []

    for file in os.listdir(input_folder):
        if file.endswith(".wav"):
            input_path = os.path.join(input_folder, file)
            output_path = os.path.join(output_folder, file)

            result = preprocess_audio(input_path, output_path)

            if result["status"]:
                success += 1
            else:
                failed.append({
                    "file": file,
                    "reason": result["message"]
                })

    return {
        "processed": success,
        "failed_count": len(failed),
        "failed_files": failed
    }
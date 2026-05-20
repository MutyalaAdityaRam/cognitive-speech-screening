# feature_extraction.py

import librosa
import numpy as np
import pandas as pd
import re

# ================= TEXT CLEAN =================
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s']", "", text)
    return text

# ================= AUDIO FEATURE FUNCTIONS =================

def extract_pause_features(audio, sr):
    energy = np.abs(audio)
    silence = energy < 0.02
    total_pause = np.sum(silence) / sr
    total_speech = len(audio)/sr - total_pause
    return {
        "total_pause": total_pause,
        "total_speech": total_speech,
        "speech_to_pause_ratio": total_speech / (total_pause + 1e-6)
    }

def extract_speech_rate(audio_path, text):
    duration = librosa.get_duration(path=audio_path)
    words = len(text.split())
    return words / (duration + 1e-6)

def extract_mfcc(audio, sr):
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
    return np.mean(mfcc, axis=1), np.std(mfcc, axis=1)

def extract_pitch(audio, sr):
    pitches, _ = librosa.piptrack(y=audio, sr=sr)
    pitch_vals = pitches[pitches > 0]
    if len(pitch_vals) == 0:
        return 0, 0
    return np.mean(pitch_vals), np.std(pitch_vals)

def extract_energy(audio):
    energy = np.square(audio)
    return np.mean(energy), np.var(energy)

def extract_text_features(text):
    words = text.split()
    total_words = len(words)
    avg_word_len = np.mean([len(w) for w in words]) if words else 0
    sentences = re.split(r'[.!?]', text)
    avg_sentence_len = np.mean([len(s.split()) for s in sentences if s]) if sentences else 0

    return (
        len(set(words)) / (total_words + 1e-6),
        total_words,
        avg_word_len,
        avg_sentence_len,
        0, 0, 0
    )

def extract_articulation_rate(total_words, speech_time):
    return total_words / (speech_time + 1e-6)

def extract_advanced_audio(audio, sr):
    return {"zcr": np.mean(librosa.feature.zero_crossing_rate(audio))}

def extract_audio_dynamics(audio, sr):
    return {"rms_std": np.std(librosa.feature.rms(y=audio))}

def extract_pitch_contour(audio, sr):
    return {"pitch_range": np.ptp(audio)}

def extract_spectral_features(audio, sr):
    return {"spectral_centroid": np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))}

def extract_text_advanced(text):
    words = text.split()
    return {"avg_word_length": np.mean([len(w) for w in words]) if words else 0}

# ================= LINGUISTIC =================
def extract_linguistic_features(text):
    words = text.split()
    if not words:
        return {}

    total = len(words)
    unique = len(set(words))

    return {
        "unique_ratio": unique / total,
        "sentence_length_max": max([len(s.split()) for s in re.split(r'[.!?]', text) if s] or [0])
    }

# ================= MAIN =================
def extract_features(audio_path, transcript, tfidf_vectorizer):

    audio, sr = librosa.load(audio_path, sr=16000)
    text = clean_text(transcript)

    pause_feats = extract_pause_features(audio, sr)
    speech_rate = extract_speech_rate(audio_path, text)

    mfcc_mean, mfcc_std = extract_mfcc(audio, sr)
    pitch_mean, pitch_std = extract_pitch(audio, sr)
    energy_mean, energy_var = extract_energy(audio)

    text_feats = extract_text_features(text)
    articulation_rate = extract_articulation_rate(
        text_feats[1], pause_feats["total_speech"]
    )

    advanced_audio = extract_advanced_audio(audio, sr)
    audio_dyn = extract_audio_dynamics(audio, sr)
    pitch_contour = extract_pitch_contour(audio, sr)
    spectral = extract_spectral_features(audio, sr)
    text_adv = extract_text_advanced(text)
    ling_feats = extract_linguistic_features(text)

    row = {
        "speech_rate": speech_rate,
        "articulation_rate": articulation_rate,
        "pitch_mean": pitch_mean,
        "pitch_std": pitch_std,
        "energy_mean": energy_mean,
        "energy_var": energy_var,
        **pause_feats,
        **advanced_audio,
        **audio_dyn,
        **pitch_contour,
        **spectral,
        **text_adv,
        **ling_feats
    }

    for i in range(13):
        row[f"mfcc_mean_{i+1}"] = mfcc_mean[i]
        row[f"mfcc_std_{i+1}"] = mfcc_std[i]

    (row["lexical_diversity"], row["total_words"], row["avg_word_length"],
     row["avg_sentence_length"], row["hesitation_rate"],
     row["filler_count"], row["repetition_count"]) = text_feats

    # ✅ IMPORTANT: transform only (no fit)
    tfidf_vector = tfidf_vectorizer.transform([text]).toarray()
    tfidf_df = pd.DataFrame(tfidf_vector, columns=tfidf_vectorizer.get_feature_names_out())

    df = pd.DataFrame([row])
    df = pd.concat([df, tfidf_df], axis=1)

    return df
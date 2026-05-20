import pandas as pd


class ExplanationAgent:
    def run(self, payload: dict[str, object]) -> dict[str, object]:
        raw_features = payload.get("raw_features")
        if raw_features is None:
            raw_features = payload.get("features")
        if not isinstance(raw_features, pd.DataFrame):
            return payload
        row = raw_features.iloc[0]
        observations: list[str] = []
        indicators: list[str] = []

        speech_rate = float(row.get("speech_rate", 0.0))
        total_pause = float(row.get("total_pause", 0.0))
        total_speech = float(row.get("total_speech", 0.0))
        speech_to_pause_ratio = float(row.get("speech_to_pause_ratio", 0.0))
        lexical_diversity = float(row.get("lexical_diversity", 0.0))
        avg_sentence_length = float(row.get("avg_sentence_length", 0.0))
        mfcc_mean_values = [float(row.get(f"mfcc_mean_{index}", 0.0)) for index in range(1, 14)]
        mfcc_std_values = [float(row.get(f"mfcc_std_{index}", 0.0)) for index in range(1, 14)]

        indicators.append(f"Speech rate: {speech_rate:.2f} words/second")
        indicators.append(f"Pause time: {total_pause:.2f}s across {total_speech:.2f}s of speech")
        indicators.append(f"Speech-to-pause ratio: {speech_to_pause_ratio:.2f}")
        indicators.append(f"Lexical diversity: {lexical_diversity:.2f}")
        indicators.append(f"Average sentence length: {avg_sentence_length:.2f} words")
        indicators.append(f"MFCC mean signature: {sum(mfcc_mean_values) / len(mfcc_mean_values):.2f}")
        indicators.append(f"MFCC variability: {sum(mfcc_std_values) / len(mfcc_std_values):.2f}")

        if speech_rate < 1.8:
            observations.append("Reduced speech rate may reflect slowed verbal output.")
        if total_pause > 0.35:
            observations.append("Pause duration is elevated relative to fluent reading.")
        if speech_to_pause_ratio < 2.0:
            observations.append("Speech and pause balance shows frequent interruption of continuous speech.")
        if lexical_diversity < 0.45:
            observations.append("Linguistic diversity is reduced in the transcript.")
        if avg_sentence_length < 8:
            observations.append("Sentence-level complexity is compressed.")
        if sum(mfcc_std_values) / len(mfcc_std_values) > 20:
            observations.append("MFCC variability indicates altered acoustic contouring.")

        if not observations:
            observations.append("Acoustic and linguistic markers do not show a strong disruption pattern.")

        payload["supporting_observations"] = observations
        payload["behavioral_indicators"] = indicators
        return payload


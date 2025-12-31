import csv
import os
from collections import Counter
from multiprocessing import Pool, cpu_count
from transformers import pipeline
import spacy

EMOTIONS = ["joy", "sadness", "anger", "fear", "disgust", "surprise", "neutral"]

MODEL_TO_USER_MAPPING = {
    "anger": "anger",
    "disgust": "disgust",
    "fear": "fear",
    "joy": "joy",
    "sadness": "sadness",
    "surprise": "surprise",
    "neutral": "neutral"
}

CUSTOM_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "than", "so", "because",
    "as", "of", "at", "by", "for", "with", "without", "on", "in", "to", "from",
    "that", "this", "these", "those", "is", "are", "was", "were", "be", "been",
    "being", "it", "its", "i", "me", "my", "we", "our", "you", "your",
    "he", "she", "they", "them"
}

_nlp = None
_classifier = None

def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    return _nlp

def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            return_all_scores=True
        )
    return _classifier

def preprocess(text: str) -> str:
    if not text:
        return ""
    
    nlp = get_nlp()
    doc = nlp(text.lower())
    
    tokens = [
        token.lemma_
        for token in doc
        if token.is_alpha and token.lemma_ not in CUSTOM_STOPWORDS
    ]
    
    return " ".join(tokens)


def classify(text: str):
    preprocessed = preprocess(text)
    if not preprocessed.strip():
        return "neutral", [], {e: 0.0 for e in EMOTIONS}

    classifier = get_classifier()
    results = classifier(preprocessed)
    res_list = results[0]

    scores = {e: 0.0 for e in EMOTIONS}
    for res in res_list:
        label = res["label"]
        score = res["score"]
        mapped = MODEL_TO_USER_MAPPING.get(label, "neutral")
        scores[mapped] = score

    top_emotion = max(scores, key=scores.get)
    if scores[top_emotion] < 0.50:
        top_emotion = "neutral"

    tokens = preprocessed.split()
    return top_emotion, tokens, scores


def process_row(row: dict) -> dict:
    review = row.get("movie reviews", "")
    label, tokens, scores = classify(review)

    out = dict(row)
    out["predicted_emotion"] = label
    out["token_count"] = str(len(tokens))
    out["emotion_scores"] = "|".join(f"{k}:{v:.4f}" for k, v in scores.items())
    return out


def run(input_csv: str, output_csv: str, parallel: bool = True):
    with open(input_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if parallel and len(rows) > 50:
        with Pool(processes=max(1, cpu_count() - 1)) as pool:
            processed_rows = pool.map(process_row, rows)
    else:
        processed_rows = [process_row(r) for r in rows]

    output_fieldnames = fieldnames + ["predicted_emotion", "token_count", "emotion_scores"]

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(processed_rows)

    counts = Counter(r["predicted_emotion"] for r in processed_rows)
    return counts


if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    input_path = os.path.join(base_dir, "movies.csv")
    output_path = os.path.join(base_dir, "movies_tagged.csv")

    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
    else:
        print("Processing movies...")
        counts = run(input_path, output_path, parallel=True)
        print("Emotion distribution:")
        for emotion in sorted(counts):
            print(f"  {emotion}: {counts[emotion]}")

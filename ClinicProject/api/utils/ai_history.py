# ClinicProject/api/utils/ai_history.py
from pathlib import Path
from typing import List, Dict
import pickle
import os
import numpy as np

# Try importing Django safely
try:
    from django.conf import settings  # type: ignore
    from django.apps import apps
    _HAS_SETTINGS = True
except Exception:
    _HAS_SETTINGS = False

_EMB_MODEL = None


def _get_embedding_model():
    """Lazy-load the SentenceTransformer model"""
    global _EMB_MODEL
    if _EMB_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _EMB_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError as e:
            print(f"SentenceTransformers not available: {e}")
            return None
    return _EMB_MODEL


def _get_index_dir() -> Path:
    """Decide where to store patient embedding indexes"""
    try:
        base_dir = Path(getattr(settings, "BASE_DIR", Path(__file__).resolve().parents[3]))
    except Exception:
        base_dir = Path(__file__).resolve().parents[3]
    index_dir = base_dir / "ai_index"
    index_dir.mkdir(parents=True, exist_ok=True)
    return index_dir


INDEX_DIR = _get_index_dir()


def chunk_text(text: str, max_chars: int = 1200):
    """Split long text into smaller chunks"""
    text = (text or "").strip()
    if not text:
        return []
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]


def build_index_for_patient(patient_id: int) -> Dict:
    """
    Builds embeddings and metadata for all notes of a patient.
    Works with your existing model that has fields: id, notes, patient, doctor, date.
    """
    try:
        NoteModel = apps.get_model("api", "Prescription")  # guessing your model name, adjust if different
    except Exception:
        # Try to find the right model automatically
        app_conf = apps.get_app_config("api")
        models = {m.__name__: m for m in app_conf.get_models()}
        possible = [m for n, m in models.items() if any(x in n.lower() for x in ["note", "consult", "prescription", "record"])]
        if not possible:
            return {"status": "error", "message": f"Couldn't find a note-like model in api. Available: {list(models.keys())}"}
        NoteModel = possible[0]

    # get all notes for that patient
    notes_qs = NoteModel.objects.filter(patient_id=patient_id)
    if hasattr(NoteModel, "date"):
        notes_qs = notes_qs.order_by("date")

    notes = list(notes_qs)
    if not notes:
        return {"status": "empty", "message": "No notes found for this patient."}

    texts, meta = [], []
    for n in notes:
        # pick the right text field
        content = None
        for field in ["notes", "text", "content", "body", "description"]:
            if hasattr(n, field):
                content = getattr(n, field)
                break
        if not content:
            continue

        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            meta.append({
                "note_id": n.id,
                "chunk_index": i,
                "date": str(getattr(n, "date", "")),
                "doctor": getattr(getattr(n, "doctor", None), "id", None)
            })
            texts.append(chunk)

    if not texts:
        return {"status": "empty", "message": "Notes exist but no text content found."}

    # Create embeddings
    model = _get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    # Save locally
    emb_path = INDEX_DIR / f"patient_{patient_id}_emb.npy"
    meta_path = INDEX_DIR / f"patient_{patient_id}_meta.pkl"
    np.save(str(emb_path), embeddings)
    with open(meta_path, "wb") as f:
        pickle.dump({"texts": texts, "meta": meta}, f)

    return {
        "status": "ok",
        "patient_id": patient_id,
        "num_chunks": len(texts),
        "emb_path": str(emb_path),
        "meta_path": str(meta_path)
    }


def load_index(patient_id: int):
    """Load saved embeddings and metadata"""
    emb_path = INDEX_DIR / f"patient_{patient_id}_emb.npy"
    meta_path = INDEX_DIR / f"patient_{patient_id}_meta.pkl"
    if not emb_path.exists() or not meta_path.exists():
        return None
    embeddings = np.load(str(emb_path))
    with open(meta_path, "rb") as f:
        meta_store = pickle.load(f)
    return embeddings, meta_store


def query_index(patient_id: int, query: str, top_k: int = 5):
    """Retrieve similar note chunks for a given query"""
    loaded = load_index(patient_id)
    if loaded is None:
        return {"status": "not_indexed", "hits": []}

    embeddings, meta_store = loaded
    model = _get_embedding_model()
    q_emb = model.encode([query], convert_to_numpy=True)[0]
    emb_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    q_norm = q_emb / np.linalg.norm(q_emb)
    sims = np.dot(emb_norm, q_norm)
    idxs = sims.argsort()[::-1][:top_k]

    hits = []
    for i in idxs:
        hits.append({
            "score": float(sims[i]),
            "text": meta_store["texts"][i],
            "meta": meta_store["meta"][i]
        })
    return {"status": "ok", "hits": hits}

# ClinicProject/api/views_ai.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .utils.ai_history import load_index, query_index
from transformers import pipeline

# summarizer pipeline (CPU)
SUMMARIZER = pipeline("summarization", model="google/flan-t5-small", device=-1)


def _summarize_text_list(texts, max_length=180, min_length=30):
    joined = "\n\n".join(texts)
    if len(joined) > 3800:
        joined = joined[:3800] + "..."
    out = SUMMARIZER(joined, max_length=max_length, min_length=min_length, do_sample=False)
    return out[0]["summary_text"]


@api_view(["GET"])
@permission_classes([AllowAny])   # <-- temporarily allow public access for testing
def patient_ai_summary(request, patient_id):
    """
    Returns an AI-generated summary for a given patient.
    Query params:
      - q : optional query/instruction
      - k : number of chunks to retrieve (default 6)
    """
    q = request.GET.get(
        "q",
        "Summarize the patient's clinical history and current problems in bullets: Problems, Past Medical History, Medications, Allergies, Last Visit Summary."
    )
    try:
        k = int(request.GET.get("k", 6))
    except Exception:
        k = 6

    # load index and get top-k relevant chunks
    loaded = load_index(patient_id)
    if loaded is None:
        return Response({"summary": "", "sources": [], "note": "No index found for this patient. Build index first."}, status=200)

    res = query_index(patient_id, q, top_k=k)
    if res.get("status") != "ok":
        return Response({"summary": "", "sources": [], "note": "Query failed or no hits."}, status=200)

    hits = res.get("hits", [])
    texts = [h["text"] for h in hits]

    try:
        summary = _summarize_text_list(texts)
    except Exception as e:
        return Response({"summary": "", "sources": [], "error": f"summarizer-error: {e}"}, status=500)

    sources = []
    for h in hits:
        meta = h.get("meta", {})
        snippet = h.get("text", "")[:300]
        sources.append({
            "score": h.get("score"),
            "note_id": meta.get("note_id"),
            "date": meta.get("date") or meta.get("created_at"),
            "snippet": snippet
        })

    return Response({"summary": summary, "sources": sources})

# ClinicProject/api/views_ai.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# Conditional imports to prevent crashes if dependencies are missing
try:
    from .utils.ai_history import load_index, query_index
    from transformers import pipeline
    AI_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"AI dependencies not available: {e}")
    AI_DEPENDENCIES_AVAILABLE = False
    # Create dummy functions to prevent crashes
    def load_index(*args, **kwargs):
        return None
    def query_index(*args, **kwargs):
        return {"status": "error", "message": "AI dependencies not installed"}
    def pipeline(*args, **kwargs):
        return None

# --- CORRECTIONS START HERE ---

# We cache the model in this global variable.
# It starts as None and is loaded on the first API call.
_GLOBAL_SUMMARIZER_MODEL = None

def get_summarizer():
    """
    Helper function to "lazy load" the AI model.
    It loads the model only once, the first time it's needed,
    and stores it in the global variable.
    """
    global _GLOBAL_SUMMARIZER_MODEL
    
    if not AI_DEPENDENCIES_AVAILABLE:
        print("AI dependencies not available. Cannot load summarizer.")
        return None
    
    # If the model isn't loaded yet, load it
    if _GLOBAL_SUMMARIZER_MODEL is None:
        print("AI Summarizer: Loading google/flan-t5-small model...")
        try:
            # Load the model and store it globally
            _GLOBAL_SUMMARIZER_MODEL = pipeline("summarization", model="google/flan-t5-small", device=-1)
            print("AI Summarizer: Model loaded successfully.")
        except Exception as e:
            # If loading fails, print an error and return None
            print(f"CRITICAL: Failed to load AI summarizer model. Error: {e}")
            return None
            
    # Return the cached model
    return _GLOBAL_SUMMARIZER_MODEL


def _summarize_text_list(texts, max_length=180, min_length=30):
    """Internal function to run the summarization."""
    
    # 1. Get the model using our lazy-loader
    # This will either return the cached model or load it for the first time.
    summarizer = get_summarizer()

    # 2. Check if the model loaded correctly
    if summarizer is None:
        raise Exception("AI model (flan-t5-small) could not be loaded. Check server logs.")

    # 3. Proceed with summarization
    joined = "\n\n".join(texts)
    if len(joined) > 3800:
        joined = joined[:3800] + "..."
    
    # Use the 'summarizer' variable we just got
    out = summarizer(joined, max_length=max_length, min_length=min_length, do_sample=False)
    return out[0]["summary_text"]

# --- CORRECTIONS END HERE ---


@api_view(["GET"])
@permission_classes([AllowAny])  # <-- temporarily allow public access for testing
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
        # This will now work correctly!
        summary = _summarize_text_list(texts)
    except Exception as e:
        # This will catch our "AI model... could not be loaded" error
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
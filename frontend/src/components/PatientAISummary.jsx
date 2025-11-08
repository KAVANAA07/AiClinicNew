import React, { useState } from "react";

// --- helper function: safe fetch with error handling ---
async function safeJsonFetch(url, options = {}) {
  try {
    const response = await fetch(url, {
      cache: "no-store", // prevents 304 caching
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    const text = await response.text();

    // If response is not ok, throw full response for better debugging
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${text}`);
    }

    // Try parsing JSON, fallback to readable error
    try {
      return JSON.parse(text);
    } catch (jsonErr) {
      console.error("Invalid JSON from server:", text);
      throw new Error("Server returned non-JSON response (HTML or invalid data).");
    }
  } catch (err) {
    console.error("Fetch failed:", err);
    throw err;
  }
}

export default function PatientAISummary({ patientId, token }) {
  const [summary, setSummary] = useState("");
  const [sources, setSources] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSummarize = async () => {
    setLoading(true);
    setError("");
    setSummary("");
    setSources([]);

    try {
      // ✅ Always hit backend, bypass dev-server HTML fallback
      const apiUrl = `http://localhost:5000/api/patient/${patientId}/ai_summary/?k=${Math.floor(Math.random() * 1000)}`;

      console.log("Requesting:", apiUrl);
      const data = await safeJsonFetch(apiUrl, {
        method: "GET",
        headers: {
          Authorization: `Token ${token}`,
        },
      });

      console.log("AI Summary response:", data);
      setSummary(data.summary || "No summary available.");
      setSources(data.sources || []);
    } catch (err) {
      console.error("AI Summary error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: "1.5rem" }}>
      <h4>🧠 AI Medical Summary</h4>
      <button
        onClick={handleSummarize}
        disabled={loading}
        style={{
          backgroundColor: "#007bff",
          color: "white",
          border: "none",
          borderRadius: "5px",
          padding: "6px 12px",
          cursor: "pointer",
          marginBottom: "10px",
        }}
      >
        {loading ? "Summarizing..." : "Summarize"}
      </button>

      {/* Error handling */}
      {error && (
        <div style={{ color: "red", marginTop: "10px" }}>
          <b>Error:</b> {error}
        </div>
      )}

      {/* Summary output */}
      {!error && summary && (
        <div style={{ marginTop: "1rem", background: "#f9f9f9", padding: "10px", borderRadius: "6px" }}>
          <p style={{ whiteSpace: "pre-line" }}>{summary}</p>

          {sources.length > 0 && (
            <div style={{ marginTop: "1rem" }}>
              <h5>🩺 Sources:</h5>
              <ul>
                {sources.map((s, i) => (
                  <li key={i}>
                    Note #{s.note_id} — {s.date || "Unknown date"}
                    <br />
                    <small>{s.snippet}</small>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )},
    </div>
  );
}

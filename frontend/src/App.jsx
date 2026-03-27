import { useState } from "react";
import ReactMarkdown from "react-markdown";

const STEPS = ["Searching the web...", "Analyzing sources...", "Writing report..."];

export default function App() {
  const [topic, setTopic] = useState("");
  const [report, setReport] = useState("");
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!topic.trim()) return;

    setReport("");
    setError("");
    setLoading(true);
    setStep(0);

    // Simulate step progress while waiting for API
    const interval = setInterval(() => {
      setStep((s) => (s < STEPS.length - 1 ? s + 1 : s));
    }, 4000);

    try {
      const res = await fetch("http://localhost:8000/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });

      if (!res.ok) throw new Error("Something went wrong. Try again.");
      const data = await res.json();
      setReport(data.report);
    } catch (err) {
      setError(err.message);
    } finally {
      clearInterval(interval);
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>Research & Report Agent</h1>
        <p>Enter any topic — the agent searches the web and writes a full report</p>
      </header>

      <form onSubmit={handleSubmit} className="search-form">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. Agentic AI trends 2025"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !topic.trim()}>
          {loading ? "Researching..." : "Generate Report"}
        </button>
      </form>

      {loading && (
        <div className="steps">
          {STEPS.map((s, i) => (
            <div key={i} className={`step ${i <= step ? "active" : ""}`}>
              <span className="dot">{i <= step ? "✓" : i + 1}</span>
              {s}
            </div>
          ))}
        </div>
      )}

      {error && <div className="error">{error}</div>}

      {report && (
        <div className="report">
          <div className="report-header">
            <h2>Report: {topic}</h2>
            <button
              className="download-btn"
              onClick={() => {
                const blob = new Blob([report], { type: "text/markdown" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `${topic.replace(/\s+/g, "_")}_report.md`;
                a.click();
              }}
            >
              Download .md
            </button>
          </div>
          <div className="markdown-body">
            <ReactMarkdown>{report}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

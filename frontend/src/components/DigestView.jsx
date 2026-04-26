import { useState } from "react";

const SEVERITY_EMOJI = { red: "🔴", yellow: "🟡", green: "🟢" };

export default function DigestView({ onDigest, loading, digest }) {
  const [companies, setCompanies] = useState("Salesforce, HubSpot, Zendesk");

  const handleGenerate = (demo = false) => {
    const list = companies
      .split(",")
      .map((c) => c.trim())
      .filter(Boolean);
    if (!list.length) return;
    onDigest(list, demo);
  };

  return (
    <div className="digest-container">
      <div className="digest-input">
        <label className="digest-label">
          Companies to monitor (comma-separated)
        </label>
        <input
          className="search-input"
          type="text"
          value={companies}
          onChange={(e) => setCompanies(e.target.value)}
          disabled={loading}
          placeholder="Salesforce, HubSpot, Zendesk..."
        />
        <div className="search-actions">
          <button
            className="btn-primary"
            onClick={() => handleGenerate(false)}
            disabled={loading}
          >
            {loading ? "Scanning..." : "Generate Digest →"}
          </button>
          <button
            className="btn-secondary"
            onClick={() => handleGenerate(true)}
            disabled={loading}
          >
            Demo
          </button>
        </div>
        <p className="search-hint">
          In production this runs automatically every Monday morning and is
          delivered to you as a voice briefing.
        </p>
      </div>

      {digest && (
        <div className="digest-report">
          <h3>Weekly Competitive Digest</h3>
          <p className="digest-summary">{digest.week_summary}</p>

          <div className="signals">
            {digest.signals?.map((signal, i) => (
              <div key={i} className={`signal signal-${signal.severity}`}>
                <span className="signal-emoji">
                  {SEVERITY_EMOJI[signal.severity] || "⚪"}
                </span>
                <div className="signal-content">
                  <strong>{signal.company}</strong>
                  <p>{signal.signal}</p>
                  <p className="signal-implication">{signal.implication}</p>
                  {signal.source && (
                    <a
                      href={signal.source}
                      target="_blank"
                      rel="noreferrer"
                      className="signal-source"
                    >
                      Source →
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>

          {digest.recommended_action && (
            <div className="recommended-action">
              <strong>This week's action:</strong> {digest.recommended_action}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

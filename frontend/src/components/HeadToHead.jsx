import { useState } from "react";

export default function HeadToHead({ onCompare, loading }) {
  const [companyA, setCompanyA] = useState("");
  const [companyB, setCompanyB] = useState("");

  const handleCompare = (demo = false) => {
    if (!companyA.trim() || !companyB.trim()) return;
    onCompare(companyA.trim(), companyB.trim(), demo);
  };

  return (
    <div className="head-to-head-input">
      <div className="company-inputs">
        <input
          className="search-input"
          type="text"
          placeholder="Your competitor (e.g. Salesforce)"
          value={companyA}
          onChange={(e) => setCompanyA(e.target.value)}
          disabled={loading}
        />
        <span className="vs-label">vs</span>
        <input
          className="search-input"
          type="text"
          placeholder="Another competitor (e.g. HubSpot)"
          value={companyB}
          onChange={(e) => setCompanyB(e.target.value)}
          disabled={loading}
        />
      </div>
      <div className="search-actions">
        <button
          className="btn-primary"
          onClick={() => handleCompare(false)}
          disabled={loading || !companyA.trim() || !companyB.trim()}
        >
          {loading ? "Comparing..." : "Compare →"}
        </button>
        <button
          className="btn-secondary"
          onClick={() => {
            setCompanyA("Salesforce");
            setCompanyB("HubSpot");
            onCompare("Salesforce", "HubSpot", true);
          }}
          disabled={loading}
        >
          Demo
        </button>
      </div>
    </div>
  );
}

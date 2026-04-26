export default function ReportView({ report }) {
  if (!report) return null;

  const {
    company_name,
    snapshot,
    financial_health,
    competitive_signals,
    risk_scores,
    strategic_summary,
    citations,
  } = report;

  const riskColor = (score) => {
    if (score >= 7) return "#e24b4a";
    if (score >= 4) return "#ef9f27";
    return "#1d9e75";
  };

  return (
    <div className="report">
      <div className="report-header">
        <h2>{company_name}</h2>
        <p className="strategic-summary">{strategic_summary}</p>
      </div>

      {/* Risk scores */}
      <section className="section">
        <h3>Risk Scores</h3>
        <div className="risk-grid">
          {risk_scores &&
            Object.entries(risk_scores).map(([key, val]) => (
              <div key={key} className="risk-item">
                <div className="risk-label">{key}</div>
                <div className="risk-bar-track">
                  <div
                    className="risk-bar-fill"
                    style={{
                      width: `${val * 10}%`,
                      backgroundColor: riskColor(val),
                    }}
                  />
                </div>
                <div className="risk-score">{val}/10</div>
              </div>
            ))}
        </div>
      </section>

      {/* Snapshot */}
      {snapshot && (
        <section className="section">
          <h3>Company Snapshot</h3>
          <p>{snapshot.business_model}</p>
          {snapshot.funding && (
            <p>
              <strong>Funding:</strong> {snapshot.funding}
            </p>
          )}
          {snapshot.key_executives?.length > 0 && (
            <div className="exec-list">
              <strong>Key Executives:</strong>
              <ul>
                {snapshot.key_executives.map((exec, i) => (
                  <li key={i}>{exec}</li>
                ))}
              </ul>
            </div>
          )}
          {snapshot.recent_news?.length > 0 && (
            <div className="news-list">
              <strong>Recent Signals:</strong>
              {snapshot.recent_news.map((item, i) => (
                <div key={i} className="news-item">
                  <a href={item.source} target="_blank" rel="noreferrer">
                    {item.headline}
                  </a>
                  <p className="signal-text">{item.signal}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Financial health */}
      {financial_health && (
        <section className="section">
          <h3>Financial Health</h3>
          <p>{financial_health.summary}</p>
          {financial_health.revenue_trend && (
            <p>
              <strong>Revenue trend:</strong> {financial_health.revenue_trend}
            </p>
          )}
          {financial_health.key_risks?.length > 0 && (
            <ul>
              {financial_health.key_risks.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          )}
          <p className="citation-ref">Source: {financial_health.source}</p>
        </section>
      )}

      {/* Competitive signals */}
      {competitive_signals && (
        <section className="section">
          <h3>Competitive Signals</h3>
          {competitive_signals.hiring_trends && (
            <p>
              <strong>Hiring:</strong> {competitive_signals.hiring_trends}
            </p>
          )}
          {competitive_signals.product_moves && (
            <p>
              <strong>Product:</strong> {competitive_signals.product_moves}
            </p>
          )}
          {competitive_signals.customer_sentiment && (
            <p>
              <strong>Sentiment:</strong> {competitive_signals.customer_sentiment}
            </p>
          )}
          {competitive_signals.pricing_signals && (
            <p>
              <strong>Pricing:</strong> {competitive_signals.pricing_signals}
            </p>
          )}
        </section>
      )}

      {/* Citations */}
      {citations?.length > 0 && (
        <section className="section citations">
          <h3>Sources</h3>
          {citations.map((c, i) => (
            <div key={i} className="citation">
              <span className="citation-num">[{i + 1}]</span>
              <span className="citation-claim">{c.claim}</span>
              {c.source?.startsWith("http") ? (
                <a href={c.source} target="_blank" rel="noreferrer" className="citation-link">
                  {c.source}
                </a>
              ) : (
                <span className="citation-link">{c.source}</span>
              )}
            </div>
          ))}
        </section>
      )}
    </div>
  );
}

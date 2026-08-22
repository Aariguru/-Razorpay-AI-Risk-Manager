import { FormEvent, useEffect, useMemo, useState } from "react";

type Decision = "allow" | "manual_review" | "block";
type OutcomeLabel =
  | "confirmed_fraud"
  | "false_positive"
  | "legitimate"
  | "insufficient_evidence";

type Summary = {
  total_transactions: number;
  assessed_transactions: number;
  assessment_coverage_percent: number;
  average_risk_score: number;
  allow_count: number;
  manual_review_count: number;
  block_count: number;
  review_queue_count: number;
  analyst_override_count: number;
};

type Distribution = {
  buckets: { label: string; minimum: number; maximum: number; count: number }[];
};

type Case = {
  transaction_id: string;
  customer_id: string;
  amount_paise: number;
  occurred_at: string;
  risk_score: number;
  decision: Decision;
  model_version: string;
  reasons: string[];
};

type Transaction = {
  id: string;
  external_reference: string | null;
  customer_id: string;
  payment_token: string;
  amount_paise: number;
  currency: string;
  payment_method: string;
  merchant_category: string;
  status: string;
  occurred_at: string;
  device_id: string | null;
  ip_hash: string | null;
  country_code: string;
  city: string | null;
  context: Record<string, unknown> | null;
  created_at: string;
};

type TransactionListResponse = {
  items: Transaction[];
  limit: number;
  offset: number;
  total: number;
};

type Assessment = {
  id: string;
  transaction_id: string;
  risk_score: number;
  decision: Decision;
  ml_probability: number;
  rules_score: number;
  anomaly_score: number;
  model_version: string;
  reasons: string[];
  feature_values: Record<string, number>;
  created_at: string;
};

type Investigation = {
  id: string;
  transaction_id: string;
  assessment_id: string | null;
  status: string;
  provider: string;
  recommendation: Decision;
  confidence: number;
  summary: string;
  evidence: Record<string, unknown>;
  limitations: string[];
  created_at: string;
};

type ReviewDecision = {
  id: string;
  transaction_id: string;
  assessment_id: string | null;
  decision: Decision;
  outcome_label: OutcomeLabel | null;
  analyst_id: string;
  notes: string | null;
  created_at: string;
};

type TransactionFormState = {
  external_reference: string;
  customer_id: string;
  payment_token: string;
  amount_paise: string;
  payment_method: "card" | "upi" | "netbanking" | "wallet";
  merchant_category: string;
  status: "authorized" | "captured" | "failed" | "refunded";
  occurred_at: string;
  device_id: string;
  ip_hash: string;
  country_code: string;
  city: string;
};

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
const API_URL = `${API_BASE}/api/v1`;
const decisionLabel: Record<Decision, string> = {
  allow: "Allow",
  manual_review: "Manual review",
  block: "Block",
};
const outcomeLabel: Record<OutcomeLabel, string> = {
  confirmed_fraud: "Confirmed fraud",
  false_positive: "False positive",
  legitimate: "Legitimate",
  insufficient_evidence: "Insufficient evidence",
};

const emptyTransactionForm: TransactionFormState = {
  external_reference: "",
  customer_id: "cust_demo_001",
  payment_token: "tok_demo_12345678",
  amount_paise: "49900",
  payment_method: "upi",
  merchant_category: "grocery",
  status: "captured",
  occurred_at: new Date().toISOString(),
  device_id: "device_demo_001",
  ip_hash: "demo_hash_001",
  country_code: "IN",
  city: "Bengaluru",
};

function currency(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value / 100);
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    let message = "Request failed";
    try {
      const payload = (await response.json()) as { detail?: string } | null;
      if (payload?.detail) {
        message = payload.detail;
      }
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

function ScoreBadge({ score, decision }: { score: number; decision: Decision }) {
  return <span className={`score score--${decision}`}>{score}</span>;
}

export function App() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [distribution, setDistribution] = useState<Distribution | null>(null);
  const [recentCases, setRecentCases] = useState<Case[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [latestReview, setLatestReview] = useState<ReviewDecision | null>(null);
  const [reviewDecision, setReviewDecision] = useState<Decision>("manual_review");
  const [reviewOutcome, setReviewOutcome] = useState<OutcomeLabel>("legitimate");
  const [reviewAnalystId, setReviewAnalystId] = useState("analyst_demo");
  const [reviewNotes, setReviewNotes] = useState("");
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [toast, setToast] = useState("");
  const [form, setForm] = useState<TransactionFormState>(emptyTransactionForm);

  const selectedCase = useMemo(
    () => recentCases.find((item) => item.transaction_id === selectedId) ?? null,
    [recentCases, selectedId],
  );

  async function loadDashboard() {
    setStatus("loading");
    try {
      const [summaryResult, distributionResult, recentCasesResult, transactionsResult] =
        await Promise.all([
          api<Summary>("/dashboard/summary"),
          api<Distribution>("/dashboard/risk-distribution"),
          api<{ items: Case[] }>("/dashboard/recent-assessments"),
          api<TransactionListResponse>("/transactions?limit=50&offset=0"),
        ]);

      setSummary(summaryResult);
      setDistribution(distributionResult);
      setRecentCases(recentCasesResult.items);
      setTransactions(transactionsResult.items);
      const nextSelectedId =
        transactionsResult.items[0]?.id ?? recentCasesResult.items[0]?.transaction_id ?? null;
      setSelectedId((current) => current ?? nextSelectedId);
      setStatus("ready");
      setToast("");
    } catch (error) {
      setToast(error instanceof Error ? error.message : "Unable to reach the API.");
      setStatus("error");
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setSelectedTransaction(null);
      setAssessment(null);
      setInvestigation(null);
      setLatestReview(null);
      return;
    }

    void Promise.all([
      api<Transaction>(`/transactions/${selectedId}`),
      api<Assessment>(`/transactions/${selectedId}/assessments/latest`).catch(() => null),
      api<Investigation>(`/transactions/${selectedId}/investigations/latest`).catch(() => null),
      api<ReviewDecision>(`/transactions/${selectedId}/reviews/latest`).catch(() => null),
    ])
      .then(([transactionResult, assessmentResult, investigationResult, reviewResult]) => {
        setSelectedTransaction(transactionResult);
        setAssessment(assessmentResult ?? null);
        setInvestigation(investigationResult ?? null);
        setLatestReview(reviewResult ?? null);
        setReviewDecision(assessmentResult?.decision ?? "manual_review");
        setReviewOutcome(reviewResult?.outcome_label ?? "legitimate");
        setReviewAnalystId(reviewResult?.analyst_id ?? "analyst_demo");
        setReviewNotes(reviewResult?.notes ?? "");
      })
      .catch((error: unknown) => {
        setToast(
          error instanceof Error ? error.message : "Unable to load transaction details.",
        );
      });
  }, [selectedId]);

  async function runAssessment() {
    if (!selectedId) return;
    try {
      const result = await api<Assessment>(`/transactions/${selectedId}/assessments`, {
        method: "POST",
      });
      setAssessment(result);
      setReviewDecision(result.decision);
      setToast("Risk assessment created successfully.");
      await loadDashboard();
    } catch (error) {
      setToast(error instanceof Error ? error.message : "Risk assessment could not be created.");
    }
  }

  async function runInvestigation() {
    if (!selectedId) return;
    try {
      const result = await api<Investigation>(`/transactions/${selectedId}/investigations`, {
        method: "POST",
        body: JSON.stringify({ provider: "mock" }),
      });
      setInvestigation(result);
      setToast("AI investigation completed.");
      await loadDashboard();
    } catch (error) {
      setToast(error instanceof Error ? error.message : "Investigation could not be completed.");
    }
  }

  async function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId) return;

    try {
      await api<ReviewDecision>(`/transactions/${selectedId}/reviews`, {
        method: "POST",
        body: JSON.stringify({
          decision: reviewDecision,
          outcome_label: reviewOutcome,
          analyst_id: reviewAnalystId,
          notes: reviewNotes || null,
        }),
      });
      setToast("Analyst decision recorded. No action was executed automatically.");
      await loadDashboard();
    } catch (error) {
      setToast(error instanceof Error ? error.message : "Review could not be saved.");
    }
  }

  async function createTransaction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      const payload = {
        external_reference: form.external_reference || null,
        customer_id: form.customer_id,
        payment_token: form.payment_token,
        amount_paise: Number(form.amount_paise),
        payment_method: form.payment_method,
        merchant_category: form.merchant_category,
        status: form.status,
        occurred_at: form.occurred_at,
        device_id: form.device_id || null,
        ip_hash: form.ip_hash || null,
        country_code: form.country_code,
        city: form.city || null,
      };

      const created = await api<Transaction>("/transactions", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setSelectedId(created.id);
      setForm({ ...emptyTransactionForm, occurred_at: new Date().toISOString() });
      setToast("Transaction created and selected.");
      await loadDashboard();
    } catch (error) {
      setToast(error instanceof Error ? error.message : "Transaction could not be created.");
    }
  }

  const maximumBucket = Math.max(
    ...(distribution?.buckets.map((item) => item.count) ?? [1]),
    1,
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#top">
          <span className="brand-mark">R</span>
          <span>
            Risk<span>Ops</span>
          </span>
        </a>
        <nav aria-label="Primary navigation">
          <a className="nav-item nav-item--active" href="#overview">
            Overview
          </a>
          <a className="nav-item" href="#transactions">
            Transactions
          </a>
          <a className="nav-item" href="#queue">
            Case queue
          </a>
          <a className="nav-item" href="#investigation">
            Investigations
          </a>
        </nav>
        <div className="sidebar-note">
          <span className="dot" /> Synthetic demo data only
          <br />
          Human approval required
        </div>
      </aside>

      <main id="top" className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Risk intelligence workspace</p>
            <h1>Payment risk, made explainable.</h1>
          </div>
          <button className="outline-button" onClick={() => void loadDashboard()}>
            Refresh data
          </button>
        </header>

        {status === "error" ? (
          <section className="empty-state">
            <h2>Connect the risk API to begin</h2>
            <p>{toast || "Unable to reach the API."}</p>
            <code>uvicorn app.main:app --reload --port 8000</code>
            <button onClick={() => void loadDashboard()}>Try again</button>
          </section>
        ) : (
          <>
            <section id="overview" className="metrics" aria-label="Risk overview">
              <article className="metric-card">
                <span>Transactions</span>
                <strong>{summary?.total_transactions ?? "—"}</strong>
                <small>{summary ? `${summary.assessment_coverage_percent}% assessed` : "Loading…"}</small>
              </article>
              <article className="metric-card">
                <span>Average risk</span>
                <strong>{summary ? `${summary.average_risk_score}/100` : "—"}</strong>
                <small>Latest assessment per transaction</small>
              </article>
              <article className="metric-card metric-card--review">
                <span>Review queue</span>
                <strong>{summary?.review_queue_count ?? "—"}</strong>
                <small>{summary?.manual_review_count ?? 0} recommended for review</small>
              </article>
              <article className="metric-card metric-card--block">
                <span>Blocks recommended</span>
                <strong>{summary?.block_count ?? "—"}</strong>
                <small>{summary?.analyst_override_count ?? 0} analyst overrides</small>
              </article>
            </section>

            <section className="overview-grid">
              <article className="panel chart-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Risk distribution</p>
                    <h2>Decision-ready exposure</h2>
                  </div>
                  <span className="live-pill">Live API</span>
                </div>
                <div className="bars">
                  {distribution?.buckets.map((bucket) => (
                    <div className="bar-row" key={bucket.label}>
                      <span>{bucket.label}</span>
                      <div className="bar-track">
                        <i style={{ width: `${(bucket.count / maximumBucket) * 100}%` }} />
                      </div>
                      <b>{bucket.count}</b>
                    </div>
                  )) ?? <p>Loading distribution…</p>}
                </div>
              </article>

              <article className="panel model-panel">
                <p className="eyebrow">Model guardrails</p>
                <h2>Explainable by design</h2>
                <ul>
                  <li>ML, rules, and anomaly signals are stored separately.</li>
                  <li>Every assessment carries its model version and reasons.</li>
                  <li>Agent output is a recommendation—not a payment action.</li>
                </ul>
              </article>
            </section>

            <section id="transactions" className="panel queue-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Transactions</p>
                  <h2>Live transaction inventory</h2>
                </div>
                <span>{transactions.length} total</span>
              </div>

              <div className="transaction-layout">
                <div className="transaction-table-wrap">
                  {transactions.length === 0 ? (
                    <p className="muted">No transactions available yet.</p>
                  ) : (
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Customer</th>
                            <th>Amount</th>
                            <th>Method</th>
                            <th>Status</th>
                            <th>Selected</th>
                          </tr>
                        </thead>
                        <tbody>
                          {transactions.map((transaction) => (
                            <tr
                              className={selectedId === transaction.id ? "selected" : ""}
                              key={transaction.id}
                            >
                              <td>
                                <b>{transaction.customer_id}</b>
                                <small>{transaction.id.slice(0, 8)}</small>
                              </td>
                              <td>{currency(transaction.amount_paise)}</td>
                              <td>{transaction.payment_method}</td>
                              <td>
                                <span className={`decision decision--${transaction.status === "captured" ? "allow" : transaction.status === "failed" ? "block" : "manual_review"}`}>
                                  {transaction.status}
                                </span>
                              </td>
                              <td>
                                <button
                                  className="text-button"
                                  onClick={() => setSelectedId(transaction.id)}
                                >
                                  Open
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                <form className="transaction-form" onSubmit={createTransaction}>
                  <p className="eyebrow">Create transaction</p>
                  <div className="field-grid">
                    <label>
                      Customer ID
                      <input
                        value={form.customer_id}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, customer_id: event.target.value }))
                        }
                      />
                    </label>
                    <label>
                      Payment token
                      <input
                        value={form.payment_token}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, payment_token: event.target.value }))
                        }
                      />
                    </label>
                    <label>
                      Amount (paise)
                      <input
                        type="number"
                        value={form.amount_paise}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, amount_paise: event.target.value }))
                        }
                      />
                    </label>
                    <label>
                      Payment method
                      <select
                        value={form.payment_method}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            payment_method: event.target.value as TransactionFormState["payment_method"],
                          }))
                        }
                      >
                        <option value="card">card</option>
                        <option value="upi">upi</option>
                        <option value="netbanking">netbanking</option>
                        <option value="wallet">wallet</option>
                      </select>
                    </label>
                    <label>
                      Merchant category
                      <input
                        value={form.merchant_category}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, merchant_category: event.target.value }))
                        }
                      />
                    </label>
                    <label>
                      Status
                      <select
                        value={form.status}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            status: event.target.value as TransactionFormState["status"],
                          }))
                        }
                      >
                        <option value="authorized">authorized</option>
                        <option value="captured">captured</option>
                        <option value="failed">failed</option>
                        <option value="refunded">refunded</option>
                      </select>
                    </label>
                    <label>
                      Occurred at
                      <input
                        type="datetime-local"
                        value={form.occurred_at.slice(0, 16)}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            occurred_at: new Date(event.target.value).toISOString(),
                          }))
                        }
                      />
                    </label>
                    <label>
                      Device ID
                      <input
                        value={form.device_id}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, device_id: event.target.value }))
                        }
                      />
                    </label>
                    <label>
                      Country code
                      <input
                        value={form.country_code}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, country_code: event.target.value }))
                        }
                      />
                    </label>
                    <label>
                      City
                      <input
                        value={form.city}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, city: event.target.value }))
                        }
                      />
                    </label>
                    <label>
                      External reference
                      <input
                        value={form.external_reference}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, external_reference: event.target.value }))
                        }
                      />
                    </label>
                    <label>
                      IP hash
                      <input
                        value={form.ip_hash}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, ip_hash: event.target.value }))
                        }
                      />
                    </label>
                  </div>

                  <button className="primary-button" type="submit">
                    Create transaction
                  </button>
                </form>
              </div>
            </section>

            <section id="queue" className="panel queue-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Priority queue</p>
                  <h2>Recent assessed transactions</h2>
                </div>
                <span>{recentCases.length} cases</span>
              </div>

              {recentCases.length === 0 ? (
                <p className="muted">No assessed transactions yet.</p>
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Transaction</th>
                        <th>Amount</th>
                        <th>Risk</th>
                        <th>Recommendation</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {recentCases.map((item) => (
                        <tr
                          className={selectedId === item.transaction_id ? "selected" : ""}
                          key={item.transaction_id}
                        >
                          <td>
                            <b>{item.customer_id}</b>
                            <small>{new Date(item.occurred_at).toLocaleString("en-IN")}</small>
                          </td>
                          <td>{currency(item.amount_paise)}</td>
                          <td>
                            <ScoreBadge score={item.risk_score} decision={item.decision} />
                          </td>
                          <td>
                            <span className={`decision decision--${item.decision}`}>
                              {decisionLabel[item.decision]}
                            </span>
                          </td>
                          <td>
                            <button
                              className="text-button"
                              onClick={() => setSelectedId(item.transaction_id)}
                            >
                              Investigate
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            {selectedTransaction && (
              <section id="investigation" className="case-grid">
                <article className="panel case-panel">
                  <div className="panel-heading">
                    <div>
                      <p className="eyebrow">Selected case</p>
                      <h2>{selectedTransaction.customer_id}</h2>
                      <span className="transaction-id">{selectedTransaction.id}</span>
                    </div>
                    <ScoreBadge
                      score={assessment?.risk_score ?? selectedCase?.risk_score ?? 0}
                      decision={assessment?.decision ?? selectedCase?.decision ?? "manual_review"}
                    />
                  </div>

                  <div className="data-grid">
                    <div className="detail-list">
                      <div className="detail-row">
                        <span>Payment method</span>
                        <b>{selectedTransaction.payment_method}</b>
                      </div>
                      <div className="detail-row">
                        <span>Merchant category</span>
                        <b>{selectedTransaction.merchant_category}</b>
                      </div>
                      <div className="detail-row">
                        <span>City / country</span>
                        <b>
                          {selectedTransaction.city ?? "—"} / {selectedTransaction.country_code}
                        </b>
                      </div>
                      <div className="detail-row">
                        <span>Status</span>
                        <b>{selectedTransaction.status}</b>
                      </div>
                      <div className="detail-row">
                        <span>Amount</span>
                        <b>{currency(selectedTransaction.amount_paise)}</b>
                      </div>
                    </div>

                    <div className="score-layout">
                      <div className="risk-orb">
                        <b>{assessment?.risk_score ?? selectedCase?.risk_score ?? 0}</b>
                        <span>risk score</span>
                      </div>
                      <div className="score-breakdown">
                        <div>
                          <span>ML signal</span>
                          <b>{assessment ? `${Math.round(assessment.ml_probability * 100)}%` : "—"}</b>
                        </div>
                        <div>
                          <span>Rules</span>
                          <b>{assessment?.rules_score ?? "—"}</b>
                        </div>
                        <div>
                          <span>Anomaly</span>
                          <b>{assessment?.anomaly_score ?? "—"}</b>
                        </div>
                        <div>
                          <span>Model</span>
                          <b>{assessment?.model_version ?? selectedCase?.model_version ?? "—"}</b>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="action-stack compact">
                    <button className="primary-button" onClick={() => void runAssessment()}>
                      Run risk assessment
                    </button>
                  </div>

                  <h3>Why this was flagged</h3>
                  <ul className="reason-list">
                    {(assessment?.reasons ?? selectedCase?.reasons ?? []).map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>

                  {assessment && (
                    <div className="feature-chips">
                      {Object.entries(assessment.feature_values)
                        .filter(([name]) => !name.startsWith("is_"))
                        .slice(0, 6)
                        .map(([name, value]) => (
                          <span key={name}>
                            {name.replaceAll("_", " ")}: <b>{value}</b>
                          </span>
                        ))}
                    </div>
                  )}
                </article>

                <aside className="action-stack">
                  <article className="panel agent-panel">
                    <div className="panel-heading">
                      <div>
                        <p className="eyebrow">AI investigator</p>
                        <h2>Evidence-backed recommendation</h2>
                      </div>
                      <span className="agent-icon">✦</span>
                    </div>

                    {investigation ? (
                      <>
                        <span className={`decision decision--${investigation.recommendation}`}>
                          {decisionLabel[investigation.recommendation]} · {Math.round(investigation.confidence * 100)}%
                          confidence
                        </span>
                        <p>{investigation.summary}</p>
                        <h3>Limitations</h3>
                        <ul>
                          {investigation.limitations.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                        <h3>Provider</h3>
                        <p>{investigation.provider}</p>
                        <h3>Investigation status</h3>
                        <p>{investigation.status}</p>
                      </>
                    ) : (
                      <>
                        <p>No investigation has been run for this case.</p>
                        <button className="primary-button" onClick={() => void runInvestigation()}>
                          Run investigation
                        </button>
                      </>
                    )}
                  </article>

                  <article className="panel review-panel">
                    <p className="eyebrow">Human control</p>
                    <h2>Record analyst decision</h2>

                    <form onSubmit={submitReview}>
                      <label>
                        Decision
                        <select
                          value={reviewDecision}
                          onChange={(event) => setReviewDecision(event.target.value as Decision)}
                        >
                          <option value="allow">Allow</option>
                          <option value="manual_review">Manual review</option>
                          <option value="block">Block</option>
                        </select>
                      </label>

                      <label>
                        Outcome label
                        <select
                          value={reviewOutcome}
                          onChange={(event) =>
                            setReviewOutcome(event.target.value as OutcomeLabel)
                          }
                        >
                          <option value="confirmed_fraud">confirmed_fraud</option>
                          <option value="false_positive">false_positive</option>
                          <option value="legitimate">legitimate</option>
                          <option value="insufficient_evidence">insufficient_evidence</option>
                        </select>
                      </label>

                      <label>
                        Analyst ID
                        <input
                          value={reviewAnalystId}
                          onChange={(event) => setReviewAnalystId(event.target.value)}
                        />
                      </label>

                      <label>
                        Review notes
                        <textarea
                          value={reviewNotes}
                          onChange={(event) => setReviewNotes(event.target.value)}
                          placeholder="Add evidence behind this decision…"
                        />
                      </label>

                      <button className="primary-button" type="submit">
                        Save decision
                      </button>
                    </form>

                    {latestReview && (
                      <div className="latest-review">
                        <h3>Latest review</h3>
                        <p>
                          <strong>{decisionLabel[latestReview.decision]}</strong> · {latestReview.analyst_id}
                        </p>
                        <p>{latestReview.outcome_label ? outcomeLabel[latestReview.outcome_label] : "No outcome label"}</p>
                        <small>{latestReview.notes || "No notes saved."}</small>
                      </div>
                    )}
                  </article>
                </aside>
              </section>
            )}
          </>
        )}

        {toast && <div className="toast" role="status">{toast}</div>}

        <footer>
          AI Risk Manager · Synthetic/public-compatible data only · No private Razorpay systems
          or data
        </footer>
      </main>
    </div>
  );
}

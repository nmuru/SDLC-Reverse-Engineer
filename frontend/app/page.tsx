"use client";

import { FormEvent, useEffect, useId, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function MermaidDiagram({ chart }: { chart: string }) {
  const id = useId().replace(/:/g, "");
  const [svg, setSvg] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function renderDiagram() {
      try {
        const { default: mermaid } = await import("mermaid");
        mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });
        const { svg: renderedSvg } = await mermaid.render(`mermaid-${id}`, chart);
        if (!cancelled) { setSvg(renderedSvg); setError(""); }
      } catch (err) {
        if (!cancelled) {
          setSvg("");
          setError(err instanceof Error ? err.message : "Unable to render Mermaid diagram.");
        }
      }
    }

    renderDiagram();
    return () => { cancelled = true; };
  }, [chart, id]);

  if (error) {
    return (
      <div className="mermaid-error">
        <div>Diagram could not be rendered.</div>
        <pre className="markdown-code-block"><code>{chart}</code></pre>
      </div>
    );
  }

  if (!svg) return <div className="mermaid-loading">Rendering diagram...</div>;

  return <div className="mermaid-diagram" dangerouslySetInnerHTML={{ __html: svg }} />;
}

type Phase = {
  id: string;
  label: string;
  shortLabel: string;
};

type AnalysisResult = {
  repo_url: string;
  business_purpose: string;
  business_requirements: string;
  features: string;
  software_requirements: string;
  technology_architecture: string;
  design_pattern: string;
  high_level_design: string;
  low_level_design: string;
  implementation_detail: string;
  testing_harness: string;
  future_directions: string;
};

type PhaseCompletedEvent = {
  type: "phase_completed";
  phase: string;
  phase_name: string;
  raw_analysis: string;
  raw_path: string;
  run_id: string;
};

type AnalysisCompletedEvent = {
  type: "analysis_completed";
  repo_url: string;
  run_id: string;
  completed_phases: string[];
};

type AnalysisFailedEvent = {
  type: "analysis_failed";
  repo_url: string;
  error: string;
};

type AnalysisEvent =
  | PhaseCompletedEvent
  | AnalysisCompletedEvent
  | AnalysisFailedEvent;

const phases: Phase[] = [
  { id: "business-purpose", label: "Business Purpose", shortLabel: "Purpose" },
  { id: "business-requirements", label: "Business Requirements", shortLabel: "Business Requirements" },
  { id: "features", label: "Features", shortLabel: "Features" },
  { id: "software-requirements", label: "Software Requirements", shortLabel: "Software Requirements" },
  { id: "technology-architecture", label: "Technology Architecture", shortLabel: "Architecture" },
  { id: "design-pattern", label: "Design Pattern", shortLabel: "Design Pattern" },
  { id: "high-level-design", label: "High-Level Design", shortLabel: "HLD" },
  { id: "low-level-design", label: "Low-Level Design", shortLabel: "LLD" },
  { id: "implementation-detail", label: "Implementation Detail", shortLabel: "Implementation" },
  { id: "testing-harness", label: "Testing Harness", shortLabel: "Testing" },
  { id: "future-directions", label: "Future Directions", shortLabel: "Future" },
];

const defaultSelectedPhases = [
  "software-requirements",
  "technology-architecture",
  "future-directions",
];

const phaseResultMap: Record<Phase["id"], keyof AnalysisResult> = {
  "business-purpose": "business_purpose",
  "business-requirements": "business_requirements",
  features: "features",
  "software-requirements": "software_requirements",
  "technology-architecture": "technology_architecture",
  "design-pattern": "design_pattern",
  "high-level-design": "high_level_design",
  "low-level-design": "low_level_design",
  "implementation-detail": "implementation_detail",
  "testing-harness": "testing_harness",
  "future-directions": "future_directions",
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const DEMO_REPO_URL = "https://github.com/vercel/commerce";
const DEMO_RUN_ID = "vercel-demo";
const DEMO_PHASE_IDS = phases.map((phase) => phase.id);

type Provider = {
  id: string;
  label: string;
  placeholder: string;
};

const providers: Provider[] = [
  {
    id: "openrouter",
    label: "OpenRouter",
    placeholder: "e.g. openai/gpt-5, anthropic/claude-sonnet-4",
  },
  {
    id: "openai",
    label: "OpenAI",
    placeholder: "e.g. gpt-5",
  },
  {
    id: "anthropic",
    label: "Anthropic",
    placeholder: "e.g. claude-sonnet-4-20250514",
  },
  {
    id: "google",
    label: "Google",
    placeholder: "e.g. gemini-2.5-pro",
  },
  {
    id: "custom",
    label: "Custom / OpenAI-compatible",
    placeholder: "Enter the model name",
  },
];

export default function Home() { 
 
  const [repoUrl, setRepoUrl] = useState("");
  const [provider, setProvider] = useState("openrouter");
  const [model, setModel] = useState("openrouter/free");
  const [apiKey, setApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [analysisResult, setAnalysisResult] =
    useState<AnalysisResult | null>(null);
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [activePhase, setActivePhase] = useState("business-purpose");
  const [completedPhases, setCompletedPhases] = useState<string[]>([]);
  const [completionMessages, setCompletionMessages] = useState<string[]>([]);
  const [selectedPhases, setSelectedPhases] = useState(defaultSelectedPhases);
  const [selectionView, setSelectionView] = useState<"setup" | null>(null);
  const [isDemo, setIsDemo] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDemoDocumentation() {
      try {
        const documents = await Promise.all(
          phases.map(async (phase) => {
            const response = await fetch(`/vercel-demo/${phase.id}.md`);

            if (!response.ok) {
              throw new Error(
                `Unable to load demo document: ${phase.id}.md (${response.status})`,
              );
            }

            return [phase.id, await response.text()] as const;
          }),
        );

        if (cancelled) return;

        const result: AnalysisResult = {
          repo_url: DEMO_REPO_URL,
          business_purpose: "",
          business_requirements: "",
          features: "",
          software_requirements: "",
          technology_architecture: "",
          design_pattern: "",
          high_level_design: "",
          low_level_design: "",
          implementation_detail: "",
          testing_harness: "",
          future_directions: "",
        };

        for (const [phaseId, content] of documents) {
          const resultKey = phaseResultMap[phaseId as Phase["id"]];
          result[resultKey] = content;
        }

        setAnalysisResult(result);
        setError("");
      } catch (err) {
        if (cancelled) return;

        console.error("Unable to load Vercel Commerce demo:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load the Vercel Commerce demo documentation.",
        );
      }
    }

    loadDemoDocumentation();

    return () => {
      cancelled = true;
    };
  }, []);

  function viewDemo() {
    if (!analysisResult) {
      setError(
        "The Vercel Commerce example is still loading. Please try again in a moment.",
      );
      return;
    }

    setError("");
    setRepoUrl(DEMO_REPO_URL);
    setRunId(DEMO_RUN_ID);
    setIsDemo(true);
    setAnalysisStarted(true);
    setAnalysisComplete(true);
    setCompletedPhases(DEMO_PHASE_IDS);
    setCompletionMessages([]);
    setActivePhase("business-purpose");
    setSelectionView(null);
  }

  async function analyze(event: FormEvent) {
    event.preventDefault();

    if (!provider || !model.trim() || !apiKey.trim()) {
      setError("Enter an AI provider, model, and API key before starting.");
      return;
    }

    if (selectedPhases.length === 0) {
      setError("Select at least one SDLC phase before starting the analysis.");
      return;
    }

    setLoading(true);
    setIsDemo(false);
    setAnalysisStarted(true);
    setSelectionView(null);
    setAnalysisComplete(false);
    if (!analysisStarted) {
      setCompletedPhases([]);
      setCompletionMessages([]);
      setActivePhase("business-purpose");
      setAnalysisResult(null);
    }
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: "POST",
        headers: {
          Accept: "text/event-stream",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          repo_url: repoUrl,
          selected_phases: selectedPhases,
          work_id: runId || null,
          provider,
          model,
          api_key: apiKey,
        }),
      });

      if (!response.ok) {
        let message = "Analysis failed.";

        try {
          const data = await response.json();
          if (typeof data?.detail === "string") {
            message = data.detail;
          }
        } catch {
          // The response may not contain JSON.
        }

        throw new Error(message);
      }

      if (!response.body) {
        throw new Error("The analysis stream was not available.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";

        for (const eventBlock of events) {
          const dataLines = eventBlock
            .split("\n")
            .filter((line) => line.startsWith("data:"))
            .map((line) => line.slice(5).trim());

          if (dataLines.length === 0) {
            continue;
          }

          const eventData = dataLines.join("\n");

          let event: AnalysisEvent;

          try {
            event = JSON.parse(eventData) as AnalysisEvent;
          } catch {
            console.error("Invalid analysis event:", eventData);
            continue;
          }

          if (event.type === "phase_completed") {
            setRunId(event.run_id);
            setCompletionMessages((previous) =>
              previous.includes(event.phase_name)
                ? previous
                : [...previous, `${event.phase_name} phase completed`],
            );
            const resultKey = phaseResultMap[
              event.phase as Phase["id"]
            ];

            if (resultKey) {
              setAnalysisResult((previous) => ({
                repo_url: repoUrl,
                business_purpose: previous?.business_purpose ?? "",
                business_requirements:
                  previous?.business_requirements ?? "",
                features: previous?.features ?? "",
                software_requirements:
                  previous?.software_requirements ?? "",
                technology_architecture:
                  previous?.technology_architecture ?? "",
                design_pattern: previous?.design_pattern ?? "",
                high_level_design: previous?.high_level_design ?? "",
                low_level_design: previous?.low_level_design ?? "",
                implementation_detail:
                  previous?.implementation_detail ?? "",
                testing_harness: previous?.testing_harness ?? "",
                future_directions: previous?.future_directions ?? "",
                [resultKey]: event.raw_analysis,
              }));

              setCompletedPhases((previous) =>
                previous.includes(event.phase)
                  ? previous
                  : [...previous, event.phase],
              );

              setActivePhase(event.phase);
            }
          } else if (event.type === "analysis_completed") {
            setRunId(event.run_id);
            setAnalysisComplete(true);
            setLoading(false);
          } else if (event.type === "analysis_failed") {
            setError(event.error);
            setAnalysisComplete(false);
            setLoading(false);
          }
        }
      }
    } catch (err) {
      console.error("Analysis request failed:", err);

      const message =
        err instanceof Error ? err.message : "Analysis failed.";

      setError(message);
      setAnalysisComplete(false);
      setLoading(false);
    }
  }

  function resetAnalysis() {
    setAnalysisStarted(false);
    setIsDemo(false);
    setAnalysisComplete(false);
    setCompletedPhases([]);
    setCompletionMessages([]);
    setRepoUrl("");
    setProvider("openrouter");
    setModel("z-ai/glm-5.3-flash");
    setApiKey("");
    setShowApiKey(false);
    setSelectedPhases(defaultSelectedPhases);
    setSelectionView(null);
    setActivePhase("business-purpose");
    setAnalysisResult(null);
    setError("");
    setLoading(false);
  }

  const activePhaseDefinition =
    phases.find((phase) => phase.id === activePhase) ?? phases[0];

  const activeResultKey = phaseResultMap[activePhaseDefinition.id];

  const activeResult =
    analysisResult && activeResultKey
      ? analysisResult[activeResultKey]
      : "";

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand">ReverseEngineer-SDLC</div>
          <div className="tagline">
            Repository → Software Engineering Dossier
          </div>
        </div>

        {analysisStarted && repoUrl && (
          <div className="repo-pill" title={repoUrl}>
            {repoUrl.replace(/^https?:\/\//, "")}
          </div>
        )}
      </header>

      {!analysisStarted ? (
        <main className="landing">
          <div className="landing-card">
            <div className="eyebrow">
              AI SOFTWARE REVERSE ENGINEERING
            </div>

            <h1>
              Turn a GitHub repository into an SDLC dossier.
            </h1>

            <p className="landing-copy">
                Submit a repository URL to progressively reconstruct its business purpose,
                business requirements, features, software requirements, architecture,
                design, implementation, testing strategy, and future directions. If you
                are enhancing an application through a spec-driven development approach,
                you can use this app to reverse engineer the existing codebase and build
                specifications that support further development.
            </p>
            <fieldset
              className="phase-selection"
              style={{ marginTop: 28 }}
            >
              <legend>AI model</legend>

              <div style={{ display: "grid", gap: 14 }}>
                <label style={{ display: "grid", gap: 7 }}>
                  <span style={{ fontSize: 13, fontWeight: 700 }}>
                    Provider
                  </span>
                  <select
                    value={provider}
                    onChange={(event) => setProvider(event.target.value)}
                    disabled={loading}
                    aria-label="AI provider"
                    style={{
                      width: "100%",
                      padding: "12px 13px",
                      border: "1px solid #cfd4da",
                      borderRadius: 9,
                      outline: "none",
                      color: "var(--text)",
                      background: "white",
                    }}
                  >
                    {providers.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.label}
                      </option>
                    ))}
                  </select>
                </label>

                <label style={{ display: "grid", gap: 7 }}>
                  <span style={{ fontSize: 13, fontWeight: 700 }}>
                    Model
                  </span>
                  <input
                    value={model}
                    onChange={(event) => setModel(event.target.value)}
                    placeholder={
                      providers.find((item) => item.id === provider)
                        ?.placeholder ?? "Enter the model name"
                    }
                    disabled={loading}
                    required
                    aria-label="AI model"
                    autoComplete="off"
                    style={{
                      width: "100%",
                      padding: "12px 13px",
                      border: "1px solid #cfd4da",
                      borderRadius: 9,
                      outline: "none",
                      color: "var(--text)",
                      background: "white",
                    }}
                  />
                </label>

                <label style={{ display: "grid", gap: 7 }}>
                  <span style={{ fontSize: 13, fontWeight: 700 }}>
                    API key
                  </span>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      value={apiKey}
                      onChange={(event) => setApiKey(event.target.value)}
                      type={showApiKey ? "text" : "password"}
                      placeholder="Enter your API key"
                      disabled={loading}
                      required
                      aria-label="AI provider API key"
                      autoComplete="off"
                      style={{
                        minWidth: 0,
                        flex: 1,
                        padding: "12px 13px",
                        border: "1px solid #cfd4da",
                        borderRadius: 9,
                        outline: "none",
                        color: "var(--text)",
                        background: "white",
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey((value) => !value)}
                      disabled={loading}
                      aria-label={showApiKey ? "Hide API key" : "Show API key"}
                      style={{
                        padding: "0 13px",
                        border: "1px solid var(--border)",
                        borderRadius: 9,
                        background: "white",
                        color: "var(--text)",
                        fontWeight: 700,
                      }}
                    >
                      {showApiKey ? "Hide" : "Show"}
                    </button>
                  </div>
                </label>

                <p
                  style={{
                    margin: 0,
                    color: "var(--muted)",
                    fontSize: 12,
                    lineHeight: 1.5,
                  }}
                >
                  Your API key is used for this analysis request and is not
                  saved by this frontend.
                </p>
              </div>
            </fieldset>

            <form onSubmit={analyze} className="repo-form">
              <input
                value={repoUrl}
                onChange={(event) => setRepoUrl(event.target.value)}
                placeholder="https://github.com/owner/repository"
                type="url"
                required
                aria-label="GitHub repository URL"
              />

              <button type="submit" disabled={loading}>
                {loading ? "Reverse engineering..." : "Reverse engineer"}
              </button>
            </form>

            <fieldset className="phase-selection">
              <legend>Select SDLC phases</legend>
              <div className="phase-selection-grid">
                {phases.map((phase) => (
                  <label key={phase.id} className="phase-option">
                    <input
                      type="checkbox"
                      checked={selectedPhases.includes(phase.id)}
                      onChange={() =>
                        setSelectedPhases((previous) =>
                          previous.includes(phase.id)
                            ? previous.filter((id) => id !== phase.id)
                            : [...previous, phase.id],
                        )
                      }
                      disabled={loading}
                    />
                    <span>{phase.label}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <button
              type="button"
              onClick={viewDemo}
              disabled={loading || !analysisResult}
              style={{
                width: "100%",
                marginBottom: 12,
                padding: "14px 16px",
                border: "1px solid var(--accent)",
                borderRadius: 10,
                background: "var(--accent)",
                color: "white",
                fontWeight: 800,
                fontSize: 15,
                cursor: loading || !analysisResult ? "not-allowed" : "pointer",
                opacity: loading || !analysisResult ? 0.65 : 1,
              }}
            >
              View Vercel Commerce example
            </button>

            <p
              style={{
                margin: "0 0 16px",
                color: "var(--muted)",
                fontSize: 13,
                lineHeight: 1.55,
              }}
            >
              You can explore a completed eleven-phase example before analyzing your own repository. 
              The Vercel Commerce analysis made approximately 230 AI requests and consumed 7.31 million tokens. 
              When run using the openrouter/free model, the recorded cost was approximately $0.03. 
              Actual usage and cost for another repository will vary with repository size, selected phases, 
              model, provider, and applicable free-tier limits.
            </p>



            <div className="landing-note">
              Analysis is performed by the backend coding-agent pipeline.
            </div>

          </div>
        </main>
      ) : (
        <div className="workspace">
          <aside className="sidebar">
            <div className="sidebar-heading">SDLC Dossier</div>

            <div className="progress-label">
              {loading
                ? `${completedPhases.length} of ${selectedPhases.length} phases completed`
                : analysisComplete
                  ? "Analysis complete"
                  : error
                    ? `${completedPhases.length} phase${
                        completedPhases.length === 1 ? "" : "s"
                      } completed before failure`
                    : "Analysis failed"}
            </div>

            <nav className="phase-nav" aria-label="SDLC phases">
              <button
                className={`phase-tab selection-tab ${selectionView === "setup" ? "active" : ""}`}
                onClick={() => setSelectionView("setup")}
              >
                <span className="phase-number">00</span>
                <span className="phase-name">Repository & phases</span>
                <span className="phase-status">•</span>
              </button>
              {phases.map((phase, index) => {
                const complete = completedPhases.includes(phase.id);
                const available = complete;

                return (
                  <button
                    key={phase.id}
                    className={`phase-tab ${
                      activePhase === phase.id ? "active" : ""
                    } ${!available ? "locked" : ""}`}
                    onClick={() => {
                      if (available) {
                        setSelectionView(null);
                        setActivePhase(phase.id);
                      }
                    }}
                    disabled={!available}
                  >
                    <span className="phase-number">
                      {String(index + 1).padStart(2, "0")}
                    </span>

                    <span className="phase-name">
                      {phase.label}
                    </span>

                    <span
                      className={`phase-status ${
                        complete ? "done" : ""
                      }`}
                    >
                      {complete ? "✓" : "•"}
                    </span>
                  </button>
                );
              })}
            </nav>

            <button
              className="new-analysis"
              onClick={resetAnalysis}
            >
              + New repository
            </button>
          </aside>

          <main className="content">
            {selectionView === "setup" ? (
              <section className="selection-panel">
                <div className="eyebrow">ANALYSIS SETUP</div>
                <h1>Turn a GitHub repository into an SDLC dossier.</h1>

                <fieldset className="phase-selection" style={{ marginTop: 28 }}>
                  <legend>AI model</legend>
                  <div style={{ display: "grid", gap: 14 }}>
                    <label style={{ display: "grid", gap: 7 }}>
                      <span style={{ fontSize: 13, fontWeight: 700 }}>Provider</span>
                      <select
                        value={provider}
                        onChange={(event) => setProvider(event.target.value)}
                        disabled={loading}
                        aria-label="AI provider"
                        style={{ width: "100%", padding: "12px 13px", border: "1px solid #cfd4da", borderRadius: 9, outline: "none", color: "var(--text)", background: "white" }}
                      >
                        {providers.map((item) => (
                          <option key={item.id} value={item.id}>{item.label}</option>
                        ))}
                      </select>
                    </label>

                    <label style={{ display: "grid", gap: 7 }}>
                      <span style={{ fontSize: 13, fontWeight: 700 }}>Model</span>
                      <input
                        value={model}
                        onChange={(event) => setModel(event.target.value)}
                        placeholder={providers.find((item) => item.id === provider)?.placeholder ?? "Enter the model name"}
                        disabled={loading}
                        required
                        aria-label="AI model"
                        autoComplete="off"
                        style={{ width: "100%", padding: "12px 13px", border: "1px solid #cfd4da", borderRadius: 9, outline: "none", color: "var(--text)", background: "white" }}
                      />
                    </label>

                    <label style={{ display: "grid", gap: 7 }}>
                      <span style={{ fontSize: 13, fontWeight: 700 }}>API key</span>
                      <div style={{ display: "flex", gap: 8 }}>
                        <input
                          value={apiKey}
                          onChange={(event) => setApiKey(event.target.value)}
                          type={showApiKey ? "text" : "password"}
                          placeholder="Enter your API key"
                          disabled={loading}
                          required
                          aria-label="AI provider API key"
                          autoComplete="off"
                          style={{ minWidth: 0, flex: 1, padding: "12px 13px", border: "1px solid #cfd4da", borderRadius: 9, outline: "none", color: "var(--text)", background: "white" }}
                        />
                        <button
                          type="button"
                          onClick={() => setShowApiKey((value) => !value)}
                          disabled={loading}
                          aria-label={showApiKey ? "Hide API key" : "Show API key"}
                          style={{ padding: "0 13px", border: "1px solid var(--border)", borderRadius: 9, background: "white", color: "var(--text)", fontWeight: 700 }}
                        >
                          {showApiKey ? "Hide" : "Show"}
                        </button>
                      </div>
                    </label>

                    <p style={{ margin: 0, color: "var(--muted)", fontSize: 12, lineHeight: 1.5 }}>
                      Your API key is used for this analysis request and is not saved by this frontend.
                    </p>
                  </div>
                </fieldset>

                <form onSubmit={analyze} className="repo-form">
                  <input
                    value={repoUrl}
                    onChange={(event) => setRepoUrl(event.target.value)}
                    placeholder="https://github.com/owner/repository"
                    type="url"
                    required
                    aria-label="GitHub repository URL"
                    disabled={loading}
                  />
                  <button type="submit" disabled={loading}>
                    {loading ? "Reverse engineering..." : "Reverse engineer"}
                  </button>
                </form>

                <fieldset className="phase-selection">
                  <legend>Select SDLC phases</legend>
                  <div className="phase-selection-grid">
                    {phases.map((phase) => {
                      const complete = completedPhases.includes(phase.id);
                      return (
                        <label key={phase.id} className={`phase-option ${complete ? "phase-option-disabled" : ""}`}>
                          <input
                            type="checkbox"
                            checked={selectedPhases.includes(phase.id)}
                            disabled={complete || loading}
                            onChange={() =>
                              setSelectedPhases((previous) =>
                                previous.includes(phase.id)
                                  ? previous.filter((id) => id !== phase.id)
                                  : [...previous, phase.id],
                              )
                            }
                          />
                          <span>{phase.label}{complete ? " (completed)" : ""}</span>
                        </label>
                      );
                    })}
                  </div>
                </fieldset>

                <div className="landing-note">
                  Analysis is performed by the backend coding-agent pipeline.
                </div>
              </section>
                        ) : error ? (
              <>
                {analysisResult && completedPhases.length > 0 && activeResult ? (
                  <section className="dossier-content">
                    <div className="eyebrow">
                      PARTIAL ANALYSIS
                    </div>

                    <h2>{activePhaseDefinition.label}</h2>

                    <p className="section-intro">
                      {completedPhases.length} of {phases.length} phases
                      completed. The analysis stopped because the
                      remaining work could not be completed.
                    </p>

                    <article className="evidence-card markdown-content">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          code({ className, children, ...props }) {
                            if (/language-mermaid/.test(className || "")) {
                              return <MermaidDiagram chart={String(children).replace(/\n$/, "")} />;
                            }
                            return <code className={className} {...props}>{children}</code>;
                          },
                        }}
                      >
                        {activeResult}
                      </ReactMarkdown>
                    </article>
                  </section>
                ) : (
                  <section className="progress-screen">
                    <div>
                      <div className="eyebrow">
                        ANALYSIS FAILED
                      </div>

                      <h1>
                        The repository could not be fully analyzed.
                      </h1>

                      <p>{error}</p>
                    </div>
                  </section>
                )}

                {completedPhases.length > 0 && (
                  <div className="section-intro">
                    {error}
                  </div>
                )}
              </>
            ) : isDemo ? (
              <>
                <section className="completion-banner">
                  <div>
                    <div className="eyebrow">
                      EXAMPLE DOCUMENTATION
                    </div>

                    <h1>
                      Vercel Commerce software dossier
                    </h1>

                    <p>
                      Browse the pre-generated eleven-phase reverse-engineering
                      documentation. Use “+ New repository” to analyze your own
                      GitHub repository.
                    </p>
                  </div>

                  <div className="completion-mark">
                    ✓
                  </div>
                </section>

                <section className="dossier-content">
                  <div className="eyebrow">
                    STAGE{" "}
                    {String(
                      phases.findIndex(
                        (phase) =>
                          phase.id === activePhase,
                      ) + 1,
                    ).padStart(2, "0")}
                  </div>

                  <h2>
                    {activePhaseDefinition.label}
                  </h2>

                  <p className="section-intro">
                    Pre-generated reverse-engineering documentation for the
                    Vercel Commerce repository.
                  </p>

                  <article className="evidence-card markdown-content">
                    {activeResult ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          code({ className, children, ...props }) {
                            if (/language-mermaid/.test(className || "")) {
                              return (
                                <MermaidDiagram
                                  chart={String(children).replace(/\n$/, "")}
                                />
                              );
                            }

                            return (
                              <code className={className} {...props}>
                                {children}
                              </code>
                            );
                          },
                        }}
                      >
                        {activeResult}
                      </ReactMarkdown>
                    ) : (
                      <div className="mermaid-loading">
                        Loading Vercel Commerce documentation...
                      </div>
                    )}
                  </article>
                </section>
              </>
            ) : analysisResult && activeResult ? (
              <>
                {analysisComplete ? (
                  <section className="completion-banner">
                    <div>
                      <div className="eyebrow">
                        REVERSE ENGINEERING COMPLETE
                      </div>

                      <h1>
                        Your software dossier is ready.
                      </h1>

                      <p>
                        Visit the individual SDLC tabs on the left
                        to explore the reconstructed system.
                      </p>
                    </div>

                    <div className="completion-mark">
                      ✓
                    </div>

                    {runId && analysisComplete && !isDemo && (
                      <a
                        className="download-button"
                        href={`${API_BASE_URL}/api/analysis/${runId}/download`}
                        download="sdlc-documentation.zip"
                        aria-label="Download SDLC documentation ZIP"
                      >
                        Download ZIP
                      </a>
                    )}
                  </section>
                ) : (
                  <section className="progress-screen">
                    <div className="spinner" />

                    <div>
                      <div className="eyebrow">
                        ANALYSIS IN PROGRESS
                      </div>

                      <h1>
                        Results are arriving progressively
                      </h1>

                      <p>
                        {completedPhases.length} of {phases.length} phases
                        have completed. You can read completed phases
                        while the remaining phases continue running.
                      </p>
                    </div>
                  </section>
                )}

                <section className="dossier-content">
                  <div className="eyebrow">
                    STAGE{" "}
                    {String(
                      phases.findIndex(
                        (phase) =>
                          phase.id === activePhase,
                      ) + 1,
                    ).padStart(2, "0")}
                  </div>

                  <h2>
                    {activePhaseDefinition.label}
                  </h2>

                  <p className="section-intro">
                    Analysis returned by the backend coding-agent
                    pipeline for this SDLC phase.
                  </p>

                  <article className="evidence-card markdown-content">
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          code({ className, children, ...props }) {
                            if (/language-mermaid/.test(className || "")) {
                              return <MermaidDiagram chart={String(children).replace(/\n$/, "")} />;
                            }
                            return <code className={className} {...props}>{children}</code>;
                          },
                        }}
                      >
                      {activeResult}
                    </ReactMarkdown>
                  </article>
                </section>
              </>
            ) : loading ? (
              <section className="progress-screen">
                <div className="spinner" />

                <div>
                  <div className="eyebrow">
                    ANALYSIS IN PROGRESS
                  </div>

                  <h1>
                    Reverse engineering the repository
                  </h1>

                  <p>
                    The backend coding agent is analyzing the
                    repository. Completed phases will appear here
                    as soon as they are ready.
                  </p>

                  {completionMessages.length > 0 && (
                    <div className="completion-messages" aria-live="polite">
                      {completionMessages.map((message) => (
                        <div key={message}>{message}</div>
                      ))}
                    </div>
                  )}
                </div>
              </section>
            ) : null}
          </main>
        </div>
      )}
    </div>
  );
}
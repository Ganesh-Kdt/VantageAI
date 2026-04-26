import { useState, useRef, useCallback } from "react";
import { analyzeCompany } from "../api";
import ReportView from "./ReportView";

const STRIP_RE = /^(research|analyze|look up|tell me about|what about|investigate|check on|find out about|get info on|what can you tell me about)\s+/i;

function extractCompany(text) {
  return text.trim().replace(STRIP_RE, "").trim() || text.trim();
}

const LOADING_STEPS = [
  "Searching live web signals...",
  "Retrieving SEC filings...",
  "Synthesising intelligence report...",
  "Scoring risk factors...",
];

export default function VoiceAgent({ demoMode = false }) {
  const [phase, setPhase] = useState("idle"); // idle | listening | processing | speaking | error | text_fallback
  const [transcript, setTranscript] = useState("");
  const [company, setCompany] = useState("");
  const [summary, setSummary] = useState("");
  const [report, setReport] = useState(null);
  const [loadingStep, setLoadingStep] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [textInput, setTextInput] = useState("");
  const audioRef = useRef(null);
  const stepTimerRef = useRef(null);
  const retryCountRef = useRef(0);

  const startLoadingSteps = () => {
    let i = 0;
    setLoadingStep(LOADING_STEPS[0]);
    stepTimerRef.current = setInterval(() => {
      i++;
      setLoadingStep(LOADING_STEPS[i % LOADING_STEPS.length]);
    }, 8000);
  };

  const stopLoadingSteps = () => clearInterval(stepTimerRef.current);

  const playTTS = useCallback((text) => {
    return new Promise((resolve) => {
      setPhase("speaking");
      fetch("/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      })
        .then((res) => {
          if (!res.ok) throw new Error("TTS unavailable");
          return res.blob();
        })
        .then((blob) => {
          const url = URL.createObjectURL(blob);
          const audio = new Audio(url);
          audioRef.current = audio;
          audio.play();
          audio.onended = () => { URL.revokeObjectURL(url); audioRef.current = null; resolve(); };
          audio.onerror = () => { URL.revokeObjectURL(url); resolve(); };
        })
        .catch(() => {
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.rate = 1.0;
          utterance.onend = resolve;
          window.speechSynthesis.speak(utterance);
        });
    });
  }, []);

  const stopAudio = () => {
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    window.speechSynthesis.cancel();
    setPhase("idle");
  };

  const runResearch = async (companyName) => {
    setPhase("processing");
    setCompany(companyName);
    setSummary("");
    setReport(null);
    startLoadingSteps();
    try {
      const res = await analyzeCompany(companyName, "first_look", demoMode);
      stopLoadingSteps();
      const fetchedReport = res.data.report;
      const strategicSummary = fetchedReport?.strategic_summary || "Research complete.";
      setReport(fetchedReport);
      setSummary(strategicSummary);
      await playTTS(`Here's the intelligence brief on ${companyName}. ${strategicSummary}`);
      setPhase("idle");
    } catch (err) {
      stopLoadingSteps();
      setErrorMsg(err.response?.data?.detail || "Research failed. Please try again.");
      setPhase("error");
    }
  };

  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setPhase("text_fallback");
      return;
    }
    setErrorMsg("");
    setTranscript("");

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setPhase("listening");
    recognition.onresult = (e) => {
      retryCountRef.current = 0;
      const heard = e.results[0][0].transcript;
      setTranscript(heard);
      runResearch(extractCompany(heard));
    };
    recognition.onerror = (e) => {
      if (e.error === "network") {
        retryCountRef.current += 1;
        if (retryCountRef.current < 2) {
          setTimeout(() => startListening(), 800);
          return;
        }
        retryCountRef.current = 0;
        setPhase("text_fallback");
        return;
      }
      setErrorMsg(`Microphone error: ${e.error}. Please try again.`);
      setPhase("error");
    };
    recognition.onend = () => {
      setPhase((prev) => (prev === "listening" ? "idle" : prev));
    };

    recognition.start();
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    const name = textInput.trim();
    if (!name) return;
    setTextInput("");
    setPhase("idle");
    runResearch(name);
  };

  return (
    <div className="voice-agent">
      {phase !== "text_fallback" && (
        <div className="voice-orb-container">
          {phase === "idle" && (
            <button className="voice-orb" onClick={startListening} aria-label="Start listening">
              <MicIcon />
            </button>
          )}
          {phase === "listening" && (
            <div className="voice-orb orb-listening">
              <div className="wave-bars"><span /><span /><span /><span /><span /></div>
            </div>
          )}
          {phase === "processing" && (
            <div className="voice-orb orb-processing">
              <div className="spinner" />
            </div>
          )}
          {phase === "speaking" && (
            <button className="voice-orb orb-speaking" onClick={stopAudio} aria-label="Stop">
              <div className="eq-bars"><span /><span /><span /><span /><span /></div>
            </button>
          )}
          {phase === "error" && (
            <button className="voice-orb orb-error" onClick={() => { setPhase("idle"); setErrorMsg(""); }}>
              <RetryIcon />
            </button>
          )}
        </div>
      )}

      <div className="voice-status">
        {phase === "idle" && !report && <p>Tap and say a company name to research</p>}
        {phase === "idle" && report && <p>Tap to research another company</p>}
        {phase === "listening" && <p className="status-listening">Listening...</p>}
        {phase === "processing" && <p className="status-processing">{loadingStep}</p>}
        {phase === "speaking" && <p className="status-speaking">Speaking — tap to stop</p>}
        {phase === "error" && <p className="status-error">{errorMsg}</p>}
      </div>

      {phase === "text_fallback" && (
        <form className="voice-text-fallback" onSubmit={handleTextSubmit}>
          <p className="status-error">Voice unavailable — type a company name instead</p>
          <div className="voice-text-row">
            <input
              className="search-input"
              type="text"
              placeholder="e.g. Stripe"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              autoFocus
            />
            <button className="btn-primary" type="submit" disabled={!textInput.trim()}>
              Research
            </button>
          </div>
          <button className="btn-secondary" style={{ marginTop: 8 }} onClick={() => { retryCountRef.current = 0; startListening(); }}>
            Try mic again
          </button>
        </form>
      )}

      {transcript && (
        <div className="voice-heard">
          <span>You said:</span> <em>"{transcript}"</em>
        </div>
      )}

      {report && (
        <>
          <div style={{ display: "flex", justifyContent: "flex-end", width: "100%", marginBottom: 8 }}>
            <button
              className="btn-secondary replay-btn"
              onClick={() => playTTS(`Here's the intelligence brief on ${company}. ${summary}`)}
              disabled={phase === "speaking" || phase === "processing"}
            >
              🔊 Replay summary
            </button>
          </div>
          <ReportView report={report} />
        </>
      )}

      <p className="voice-hint-text">
        Try: "Research Stripe" · "Tell me about HubSpot" · "Analyze Salesforce"
      </p>
    </div>
  );
}

function MicIcon() {
  return (
    <svg width="36" height="36" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.91-3c-.49 0-.9.36-.98.85C16.52 14.2 14.47 16 12 16s-4.52-1.8-4.93-4.15c-.08-.49-.49-.85-.98-.85-.61 0-1.09.54-1 1.14.49 3 2.89 5.35 5.91 5.78V20c0 .55.45 1 1 1s1-.45 1-1v-2.08c3.02-.43 5.42-2.78 5.91-5.78.1-.6-.39-1.14-1-1.14z"/>
    </svg>
  );
}

function RetryIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
      <path d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
    </svg>
  );
}

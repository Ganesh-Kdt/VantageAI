import { useState } from "react";

const VOICERUN_API_KEY = process.env.REACT_APP_VOICERUN_API_KEY;

export default function VoiceButton({ reportText, onVoiceInput }) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState("");

  // ── Voice input (browser Web Speech API → passes text to agent) ──────────
  const startListening = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Voice input not supported in this browser. Try Chrome.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);

    recognition.onresult = (e) => {
      const text = e.results[0][0].transcript;
      setTranscript(text);
      if (onVoiceInput) onVoiceInput(text);
    };

    recognition.onerror = (e) => {
      console.error("Speech recognition error:", e.error);
      setIsListening(false);
    };

    recognition.start();
  };

  // ── Voice output (VoiceRun TTS → reads report summary aloud) ─────────────
  const speakReport = async () => {
    if (!reportText) return;
    setIsSpeaking(true);

    // Truncate to ~200 words for a ~90-second briefing
    const words = reportText.split(" ").slice(0, 200).join(" ");
    const summary = words + (reportText.split(" ").length > 200 ? "..." : "");

    try {
      if (VOICERUN_API_KEY) {
        // VoiceRun TTS
        const res = await fetch("https://api.voicerun.ai/v1/tts", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${VOICERUN_API_KEY}`,
          },
          body: JSON.stringify({
            text: summary,
            voice: "nova",
            speed: 1.05,
          }),
        });

        if (!res.ok) throw new Error("VoiceRun TTS failed");

        const audioBlob = await res.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
        audio.onended = () => {
          setIsSpeaking(false);
          URL.revokeObjectURL(audioUrl);
        };
      } else {
        // Fallback: browser Web Speech API (no key needed)
        const utterance = new SpeechSynthesisUtterance(summary);
        utterance.rate = 1.05;
        utterance.onend = () => setIsSpeaking(false);
        window.speechSynthesis.speak(utterance);
      }
    } catch (err) {
      console.error("TTS error, falling back to browser speech:", err);
      // Graceful fallback
      const utterance = new SpeechSynthesisUtterance(summary);
      utterance.onend = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    }
  };

  const stopSpeaking = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  };

  return (
    <div className="voice-controls">
      <button
        className={`voice-btn ${isListening ? "listening" : ""}`}
        onClick={startListening}
        disabled={isListening || isSpeaking}
        title="Ask a follow-up question by voice"
      >
        {isListening ? "🎙 Listening..." : "🎙 Ask by voice"}
      </button>

      <button
        className={`voice-btn ${isSpeaking ? "speaking" : ""}`}
        onClick={isSpeaking ? stopSpeaking : speakReport}
        disabled={!reportText || isListening}
        title="Read the report aloud"
      >
        {isSpeaking ? "⏹ Stop" : "🔊 Read report"}
      </button>

      {transcript && (
        <p className="voice-transcript">
          Heard: <em>"{transcript}"</em>
        </p>
      )}

      {!VOICERUN_API_KEY && (
        <p className="voice-hint">
          Add REACT_APP_VOICERUN_API_KEY to .env for VoiceRun TTS.
          Using browser speech as fallback.
        </p>
      )}
    </div>
  );
}

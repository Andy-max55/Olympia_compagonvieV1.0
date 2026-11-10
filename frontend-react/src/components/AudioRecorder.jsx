import { useEffect, useRef, useState } from "react";

function stopStream(stream) {
  stream?.getTracks().forEach((track) => track.stop());
}

function AudioRecorder({ onTranscriptionResult }) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState("");
  const streamRef = useRef(null);
  const recorderRef = useRef(null);

  useEffect(() => {
    return () => {
      const recorder = recorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        recorder.onstop = null;
        recorder.stop();
      }
      stopStream(streamRef.current);
      streamRef.current = null;
      recorderRef.current = null;
    };
  }, []);

  async function sendAudio(blob) {
    setIsProcessing(true);
    setError("");
    try {
      const body = new FormData();
      body.append("audio", blob, "objectif.webm");
      const response = await fetch("/api/transcribe", {
        method: "POST",
        body,
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        const detail = typeof data?.detail === "string" ? data.detail : "La transcription a échoué.";
        throw new Error(detail);
      }
      const text = data?.text || data?.transcription || data?.transcript || "";
      if (typeof text === "string" && text.trim()) {
        onTranscriptionResult(text.trim());
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "La transcription a échoué.");
    } finally {
      setIsProcessing(false);
    }
  }

  async function startRecording() {
    setError("");
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("L'enregistrement audio n'est pas disponible sur cet appareil.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const chunks = [];
      const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : undefined;
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      recorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      recorder.onstop = () => {
        stopStream(streamRef.current);
        streamRef.current = null;
        const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
        if (blob.size > 0) {
          sendAudio(blob);
        }
      };
      recorder.start();
      setIsRecording(true);
    } catch {
      stopStream(streamRef.current);
      streamRef.current = null;
      setIsRecording(false);
      setError("Micro refusé. Autorise l'accès pour dicter l'objectif.");
    }
  }

  function stopRecording() {
    const recorder = recorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
    setIsRecording(false);
  }

  const label = isProcessing ? "Transcription…" : isRecording ? "Arrêter" : "Dicter l'objectif";

  return (
    <div className="mt-3 flex w-full min-w-0 flex-col gap-2">
      <button
        type="button"
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isProcessing}
        aria-pressed={isRecording}
        className={`min-h-12 w-full rounded-full border px-4 text-sm font-medium transition-colors disabled:opacity-60 ${
          isRecording
            ? "animate-pulse border-red-400 bg-red-600 text-white"
            : "border-white/15 bg-white/[0.04] text-gray-200 hover:bg-white/[0.08]"
        }`}
      >
        {label}
      </button>
      {error ? <p className="text-sm text-red-400">{error}</p> : null}
    </div>
  );
}

export default AudioRecorder;

import { useEffect, useRef, useState } from "react";
import {
  ArrowUp,
  Clock,
  CreditCard,
  Dumbbell,
  Flame,
  Heart,
  LogOut,
  MessageSquare,
  Mic,
  Paperclip,
  Plus,
  Settings,
  Timer,
  User,
  X,
} from "lucide-react";

const USER_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const CHAT_URL = "http://127.0.0.1:8080/api/chat/";

const DISPLAY_FONT = { fontFamily: '"Cormorant Garamond", Georgia, serif' };
const UI_FONT = { fontFamily: "Outfit, system-ui, sans-serif" };

const SUGGESTIONS = [
  {
    icon: Dumbbell,
    title: "Programme force",
    subtitle: "Construis-moi un programme de force sur 8 semaines.",
  },
  {
    icon: Heart,
    title: "Récupération",
    subtitle: "Comment optimiser ma récupération après une séance intense ?",
  },
  {
    icon: Flame,
    title: "Nutrition",
    subtitle: "Que manger avant et après l'entraînement ?",
  },
  {
    icon: Timer,
    title: "Cardio HIIT",
    subtitle: "Propose une séance HIIT de 20 minutes sans matériel.",
  },
];

const HISTORY_ITEMS = [
  { id: "force", title: "Programme force 8 semaines", when: "Hier" },
  { id: "recovery", title: "Récupération post-séance", when: "Lundi" },
  { id: "nutrition", title: "Nutrition pré-entraînement", when: "12 oct." },
];

const PROFILE_ACTIONS = [
  { id: "account", label: "Mon Compte", icon: User },
  { id: "plan", label: "Abonnement", icon: CreditCard },
  { id: "logout", label: "Déconnexion", icon: LogOut },
];

function OlympicRings() {
  return (
    <svg className="h-8 w-12 shrink-0 text-red-600" viewBox="0 0 88 54" fill="none" role="img" aria-label="Anneaux olympiques">
      <circle cx="20" cy="18" r="14" fill="none" stroke="currentColor" strokeWidth="2.2" />
      <circle cx="44" cy="18" r="14" fill="none" stroke="currentColor" strokeWidth="2.2" />
      <circle cx="68" cy="18" r="14" fill="none" stroke="currentColor" strokeWidth="2.2" />
      <circle cx="32" cy="32" r="14" fill="none" stroke="currentColor" strokeWidth="2.2" />
      <circle cx="56" cy="32" r="14" fill="none" stroke="currentColor" strokeWidth="2.2" />
    </svg>
  );
}

function SettingToggle({ label, checked, onChange }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={onChange}
      className="flex w-full items-center justify-between rounded-xl px-3 py-3 text-left text-sm text-gray-200 transition-colors hover:bg-white/5"
    >
      <span>{label}</span>
      <span className={`relative h-6 w-11 rounded-full transition-colors ${checked ? "bg-red-600" : "bg-white/10"}`}>
        <span
          className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
            checked ? "translate-x-5" : "translate-x-0.5"
          }`}
        />
      </span>
    </button>
  );
}

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [settingsPrefs, setSettingsPrefs] = useState({
    darkTheme: true,
    expertMode: false,
    notifications: true,
  });
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const profileRef = useRef(null);
  const requestId = useRef(0);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    if (!isProfileMenuOpen) {
      return undefined;
    }
    function onPointerDown(event) {
      if (!profileRef.current?.contains(event.target)) {
        setIsProfileMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, [isProfileMenuOpen]);

  useEffect(() => {
    function onKeyDown(event) {
      if (event.key !== "Escape") {
        return;
      }
      setIsProfileMenuOpen(false);
      setIsSettingsOpen(false);
      setIsHistoryOpen(false);
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  function clearSelectedFile() {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function handleNewChat() {
    requestId.current += 1;
    setMessages([]);
    setInputValue("");
    clearSelectedFile();
    setIsLoading(false);
    setIsRecording(false);
  }

  function toggleRecording() {
    setIsRecording((current) => !current);
  }

  function handleFileSelect(event) {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
  }

  function toggleSettings() {
    setIsSettingsOpen((current) => !current);
    setIsProfileMenuOpen(false);
  }

  function toggleProfileMenu() {
    setIsProfileMenuOpen((current) => !current);
  }

  function toggleHistory() {
    setIsHistoryOpen((current) => !current);
  }

  function toggleSetting(key) {
    setSettingsPrefs((current) => ({ ...current, [key]: !current[key] }));
  }

  async function handleSend(text) {
    const message = text.trim();
    if (!message || isLoading) {
      return;
    }

    const currentRequest = requestId.current + 1;
    requestId.current = currentRequest;
    setMessages((current) => [...current, { role: "user", text: message }]);
    setInputValue("");
    clearSelectedFile();
    setIsRecording(false);
    setIsLoading(true);

    try {
      const response = await fetch(CHAT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, message }),
      });
      const data = await response.json().catch(() => null);
      if (currentRequest !== requestId.current) {
        return;
      }
      if (!response.ok || typeof data?.advice !== "string" || !data.advice.trim()) {
        throw new Error("api_error");
      }
      setMessages((current) => [...current, { role: "olympia", text: data.advice.trim() }]);
    } catch (error) {
      if (currentRequest !== requestId.current) {
        return;
      }
      console.error("Olympia : échec de la requête", error);
      setMessages((current) => [
        ...current,
        {
          role: "olympia",
          text: "Je n'arrive pas à joindre le coach pour le moment. Réessayez dans un instant.",
        },
      ]);
    } finally {
      if (currentRequest === requestId.current) {
        setIsLoading(false);
      }
    }
  }

  function onSubmit(event) {
    event.preventDefault();
    handleSend(inputValue);
  }

  return (
    <div
      className="relative flex h-screen w-screen select-none overflow-hidden bg-[#0a0a0a] text-white"
      style={UI_FONT}
    >
      <div
        className="pointer-events-none absolute left-[-8rem] top-1/3 z-0 h-[28rem] w-[28rem] rounded-full bg-cyan-900/10 blur-[120px]"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute right-[-6rem] top-1/4 z-0 h-[32rem] w-[32rem] rounded-full bg-red-900/20 blur-[120px]"
        aria-hidden="true"
      />

      <aside
        className="z-30 flex h-full w-16 shrink-0 flex-col items-center justify-between border-r border-white/5 bg-[#0a0a0a]/80 py-6 backdrop-blur-md md:w-20"
        aria-label="Navigation"
      >
        <OlympicRings />
        <div className="flex flex-col items-center gap-6">
          <button
            type="button"
            onClick={handleNewChat}
            className="rounded-lg p-2 text-gray-400 transition-all hover:bg-white/5 hover:text-white"
            aria-label="Nouveau chat"
          >
            <Plus size={22} strokeWidth={1.75} />
          </button>
          <button
            type="button"
            onClick={toggleHistory}
            className={`rounded-lg p-2 transition-all hover:bg-white/5 hover:text-white ${isHistoryOpen ? "text-white" : "text-gray-400"}`}
            aria-label="Historique"
            aria-expanded={isHistoryOpen}
          >
            <Clock size={22} strokeWidth={1.75} />
          </button>
        </div>
        <div className="flex flex-col items-center gap-6">
          <button
            type="button"
            onClick={toggleSettings}
            className={`rounded-lg p-2 transition-all hover:bg-white/5 hover:text-white ${isSettingsOpen ? "text-white" : "text-gray-400"}`}
            aria-label="Paramètres"
            aria-expanded={isSettingsOpen}
          >
            <Settings size={22} strokeWidth={1.75} />
          </button>
          <div ref={profileRef} className="relative">
            <button
              type="button"
              onClick={toggleProfileMenu}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-600 text-xs font-semibold"
              aria-label="Profil"
              aria-expanded={isProfileMenuOpen}
            >
              AT
            </button>
            {isProfileMenuOpen ? (
              <div className="absolute bottom-16 left-4 z-50 w-48 rounded-xl border border-white/10 bg-[#111] p-2 shadow-2xl backdrop-blur-xl">
                {PROFILE_ACTIONS.map((action) => {
                  const Icon = action.icon;
                  return (
                    <button
                      key={action.id}
                      type="button"
                      onClick={() => setIsProfileMenuOpen(false)}
                      className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-gray-300 transition-colors hover:bg-white/5 hover:text-white"
                    >
                      <Icon size={16} strokeWidth={1.75} aria-hidden="true" />
                      {action.label}
                    </button>
                  );
                })}
              </div>
            ) : null}
          </div>
        </div>
      </aside>

      <aside
        className={`fixed bottom-0 left-16 top-0 z-40 w-64 border-r border-white/5 bg-[#0a0a0a]/95 p-4 backdrop-blur-xl transition-transform duration-300 ease-out md:left-20 ${
          isHistoryOpen
            ? "translate-x-0"
            : "pointer-events-none -translate-x-[calc(100%+4rem)] md:-translate-x-[calc(100%+5rem)]"
        }`}
        aria-hidden={!isHistoryOpen}
        inert={!isHistoryOpen}
        aria-label="Historique"
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-medium tracking-wide text-gray-200">Historique</h2>
          <button
            type="button"
            onClick={() => setIsHistoryOpen(false)}
            className="text-gray-400 transition-colors hover:text-white"
            aria-label="Fermer l'historique"
          >
            <X size={16} />
          </button>
        </div>
        <ul className="flex flex-col gap-1">
          {HISTORY_ITEMS.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className="flex w-full items-start gap-3 rounded-xl px-3 py-3 text-left transition-colors hover:bg-white/5"
              >
                <MessageSquare className="mt-0.5 shrink-0 text-red-500" size={16} strokeWidth={1.75} aria-hidden="true" />
                <span>
                  <span className="block text-sm text-gray-200">{item.title}</span>
                  <span className="mt-0.5 block text-xs text-gray-500">{item.when}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <main className="relative z-10 flex h-full flex-1 flex-col overflow-hidden">
        <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col justify-between overflow-y-auto px-4 py-6 md:px-8">
        <header className="flex w-full items-start justify-between">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-red-500">Préparation physique</p>
            <h1 className="font-serif text-5xl font-light italic" style={DISPLAY_FONT}>
              Olympia
            </h1>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-gray-300">
            <span className="h-2 w-2 rounded-full bg-green-500" aria-hidden="true" />
            Coach en ligne
          </div>
        </header>

        {messages.length === 0 ? (
          <section className="my-auto grid w-full grid-cols-1 gap-4 py-4 md:grid-cols-2" aria-label="Suggestions">
            {SUGGESTIONS.map((suggestion) => {
              const Icon = suggestion.icon;
              return (
                <button
                  key={suggestion.title}
                  type="button"
                  onClick={() => handleSend(suggestion.subtitle)}
                  className="min-h-[120px] cursor-pointer rounded-3xl border border-white/[0.05] bg-white/[0.03] p-6 text-left backdrop-blur-md transition-all hover:bg-white/[0.05]"
                >
                  <Icon className="text-red-500" size={22} strokeWidth={1.75} aria-hidden="true" />
                  <h2 className="mt-4 text-white">{suggestion.title}</h2>
                  <p className="mt-1 text-sm text-gray-400">{suggestion.subtitle}</p>
                </button>
              );
            })}
          </section>
        ) : (
          <div
            className="flex min-h-0 w-full flex-1 flex-col gap-6 overflow-y-auto py-4"
            aria-live="polite"
            aria-label="Historique de conversation"
          >
            {messages.map((message, index) =>
              message.role === "user" ? (
                <article key={`${message.role}-${index}`} className="flex justify-end">
                  <div className="max-w-[80%] rounded-3xl border border-red-500/20 bg-red-900/20 px-5 py-3 text-sm font-light leading-relaxed text-gray-100">
                    <p className="m-0 select-text whitespace-pre-wrap">{message.text}</p>
                  </div>
                </article>
              ) : (
                <article key={`${message.role}-${index}`} className="flex justify-start">
                  <div className="max-w-[80%] rounded-3xl border border-white/[0.05] bg-white/[0.03] px-5 py-3 text-sm font-light leading-relaxed text-gray-200 backdrop-blur-md">
                    <p className="m-0 select-text whitespace-pre-wrap">{message.text}</p>
                  </div>
                </article>
              ),
            )}
            {isLoading ? (
              <article className="flex justify-start" role="status" aria-label="Olympia réfléchit">
                <div className="rounded-3xl border border-white/[0.05] bg-white/[0.03] px-5 py-4 backdrop-blur-md">
                  <div className="ring-loader" aria-hidden="true">
                    <div className="ring" />
                    <div className="ring" />
                    <div className="ring" />
                    <div className="ring" />
                    <div className="ring" />
                  </div>
                </div>
              </article>
            ) : null}
            <div ref={messagesEndRef} />
          </div>
        )}

        <form className="mt-auto w-full shrink-0 pb-2 pt-4" onSubmit={onSubmit}>
          {selectedFile ? (
            <div className="mb-3 flex w-fit items-center gap-2 rounded-lg border border-white/20 bg-white/10 px-3 py-1 text-sm text-gray-300">
              <Paperclip size={14} aria-hidden="true" />
              <span className="max-w-[16rem] truncate">{selectedFile.name}</span>
              <button
                type="button"
                onClick={clearSelectedFile}
                className="text-gray-400 transition-colors hover:text-white"
                aria-label="Retirer le fichier"
              >
                <X size={14} />
              </button>
            </div>
          ) : null}
          <div className="flex w-full items-center gap-3 rounded-full border border-white/10 bg-white/[0.03] p-2 shadow-lg backdrop-blur-xl">
            <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileSelect} />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="ml-4 shrink-0 text-gray-400 transition-colors hover:text-white"
              aria-label="Pièce jointe"
            >
              <Paperclip size={18} strokeWidth={1.75} />
            </button>
            <label htmlFor="chat-input" className="sr-only">
              Votre message
            </label>
            <input
              id="chat-input"
              name="message"
              type="text"
              value={inputValue}
              onChange={(event) => setInputValue(event.target.value)}
              placeholder="Demandez à Olympia..."
              className="flex-1 select-text bg-transparent text-white placeholder-gray-500 focus:outline-none"
            />
            <button
              type="button"
              onClick={toggleRecording}
              aria-pressed={isRecording}
              aria-label={isRecording ? "Arrêter le micro" : "Micro"}
              className={`shrink-0 transition-colors ${isRecording ? "animate-pulse text-red-500" : "text-gray-400 hover:text-white"}`}
            >
              <Mic size={18} strokeWidth={1.75} />
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-600/90 text-white transition-colors hover:bg-red-500 disabled:opacity-40"
              aria-label="Envoyer"
            >
              <ArrowUp size={18} strokeWidth={2} />
            </button>
          </div>
          <p className="mt-3 text-center text-[10px] text-gray-500">Olympia peut se tromper...</p>
        </form>
        </div>
      </main>

      {isSettingsOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setIsSettingsOpen(false)}
          role="presentation"
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="settings-title"
            className="w-[400px] rounded-2xl border border-white/10 bg-[#0f0f0f] p-6 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id="settings-title" className="text-lg font-medium text-white">
              Paramètres
            </h2>
            <div className="mt-4 flex flex-col">
              <SettingToggle
                label="Thème sombre"
                checked={settingsPrefs.darkTheme}
                onChange={() => toggleSetting("darkTheme")}
              />
              <SettingToggle
                label="Mode expert"
                checked={settingsPrefs.expertMode}
                onChange={() => toggleSetting("expertMode")}
              />
              <SettingToggle
                label="Notifications"
                checked={settingsPrefs.notifications}
                onChange={() => toggleSetting("notifications")}
              />
            </div>
            <button
              type="button"
              onClick={() => setIsSettingsOpen(false)}
              className="mt-6 w-full rounded-xl border border-white/10 bg-white/5 py-2.5 text-sm text-gray-200 transition-colors hover:bg-white/10"
            >
              Fermer
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default App;

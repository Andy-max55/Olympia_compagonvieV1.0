document.addEventListener("DOMContentLoaded", () => {
  const USER_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
  const chatHistory = document.getElementById("chat-history");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatSubmit = document.getElementById("chat-submit");
  const loadingIndicator = document.getElementById("loading-indicator");
  const welcomeScreen = document.getElementById("welcome-screen");
  const dynamicSlogan = document.getElementById("dynamic-slogan");

  const SLOGANS = [
    "La discipline bat le talent.",
    "Construisons votre physique.",
    "Chaque répétition compte.",
    "L'excellence est une habitude.",
    "Le progrès aime la constance.",
    "Aujourd'hui, on élève le standard.",
  ];

  let sloganIndex = 0;
  let sloganTimer = null;

  function rotateSlogan() {
    if (!dynamicSlogan) {
      return;
    }
    dynamicSlogan.classList.add("is-fading");
    window.setTimeout(() => {
      sloganIndex = (sloganIndex + 1) % SLOGANS.length;
      dynamicSlogan.textContent = SLOGANS[sloganIndex];
      dynamicSlogan.classList.remove("is-fading");
    }, 600);
  }

  function startSloganRotation() {
    if (!dynamicSlogan) {
      return;
    }
    sloganTimer = window.setInterval(rotateSlogan, 30000);
  }

  function hideWelcomeScreen() {
    if (!welcomeScreen) {
      return;
    }
    welcomeScreen.style.display = "none";
    if (sloganTimer !== null) {
      window.clearInterval(sloganTimer);
      sloganTimer = null;
    }
  }

  startSloganRotation();

  if (!chatHistory || !chatForm || !chatInput || !chatSubmit || !loadingIndicator) {
    console.error("Olympia : un élément du DOM est introuvable.");
    return;
  }

  if (typeof marked !== "undefined" && typeof marked.setOptions === "function") {
    marked.setOptions({ gfm: true, breaks: true });
  }

  function extractAdvice(data) {
    if (!data || typeof data !== "object") {
      return "";
    }
    const raw = data.advice ?? data.response ?? data.message ?? "";
    return typeof raw === "string" ? raw.trim() : "";
  }

  function parseMarkdown(markdown) {
    const source = String(markdown);
    if (typeof marked === "undefined") {
      return source;
    }
    if (typeof marked.parse !== "function") {
      if (typeof marked === "function") {
        return marked(source);
      }
      throw new Error("marked.parse n'est pas disponible");
    }
    const parsed = marked.parse(source);
    if (typeof parsed !== "string") {
      throw new Error("marked.parse n'a pas renvoyé de chaîne");
    }
    return parsed;
  }

  function scrollToBottom() {
    chatHistory.scrollTop = chatHistory.scrollHeight;
    const lastCard = chatHistory.lastElementChild;
    if (lastCard && typeof lastCard.scrollIntoView === "function") {
      lastCard.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }

  const OLYMPIA_BUBBLE_CLASS =
    "max-w-[88%] rounded-2xl border border-red-100 px-5 py-4 text-sm text-neutral-900 shadow-sm backdrop-blur-md";

  function showThinkingBubble() {
    const article = document.createElement("article");
    article.id = "olympia-thinking";
    article.className = "bubble-enter flex justify-start";
    article.setAttribute("role", "status");
    article.setAttribute("aria-label", "Olympia réfléchit");

    const bubble = document.createElement("div");
    bubble.className = `${OLYMPIA_BUBBLE_CLASS} ai-shimmer-bg`;

    const label = document.createElement("p");
    label.className = "animate-pulse text-xs tracking-wide text-neutral-500";
    label.style.margin = "0";
    label.textContent = "Analyse en cours...";

    bubble.append(label);
    article.append(bubble);
    chatHistory.append(article);
    scrollToBottom();
  }

  function hideThinkingBubble() {
    const thinking = document.getElementById("olympia-thinking");
    if (thinking) {
      thinking.remove();
    }
  }

  function appendUserMessage(text) {
    const article = document.createElement("article");
    article.className = "bubble-enter flex justify-end";

    const bubble = document.createElement("div");
    bubble.className =
      "max-w-[78%] rounded-3xl bg-gray-100 px-4 py-2.5 text-sm leading-relaxed text-gray-900 shadow-sm";

    const body = document.createElement("p");
    body.style.margin = "0";
    body.style.whiteSpace = "pre-wrap";
    body.textContent = text;

    bubble.append(body);
    article.append(bubble);
    chatHistory.append(article);
    scrollToBottom();
  }

  function appendOlympiaMessage(markdown) {
    const article = document.createElement("article");
    article.className = "bubble-enter flex justify-start";

    const bubble = document.createElement("div");
    bubble.className = `${OLYMPIA_BUBBLE_CLASS} bg-gradient-to-br from-red-50/80 to-white/40`;

    const body = document.createElement("div");
    body.className = "olympia-md";

    try {
      body.innerHTML = parseMarkdown(markdown);
    } catch (error) {
      console.error("Olympia : échec du rendu Markdown", error);
      body.textContent = "Erreur d'affichage";
    }

    bubble.append(body);
    article.append(bubble);
    chatHistory.append(article);
    scrollToBottom();
  }

  async function sendMessage(message) {
    hideWelcomeScreen();
    appendUserMessage(message);
    chatInput.value = "";
    showThinkingBubble();
    chatSubmit.disabled = true;

    try {
      const response = await fetch("/api/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, message: message }),
      });

      const data = await response.json().catch((error) => {
        console.error("Olympia : JSON invalide", error);
        return null;
      });

      if (!response.ok) {
        throw new Error("api_error");
      }

      const advice = extractAdvice(data);
      hideThinkingBubble();
      if (!advice) {
        console.error("Olympia : clé advice/response absente", data);
        appendOlympiaMessage("Erreur d'affichage");
        return;
      }

      appendOlympiaMessage(advice);
    } catch (error) {
      console.error("Olympia : échec de la requête", error);
      hideThinkingBubble();
      appendOlympiaMessage("Erreur d'affichage");
    } finally {
      hideThinkingBubble();
      chatSubmit.disabled = false;
      chatInput.focus();
    }
  }

  chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const message = chatInput.value.trim();
    if (!message) {
      return;
    }
    sendMessage(message);
  });

  chatInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      chatForm.requestSubmit();
    }
  });
});

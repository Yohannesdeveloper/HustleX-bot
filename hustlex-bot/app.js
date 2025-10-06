// Simple i18n dictionary (no server required)
const translations = {
  en: {
    appTitle: "HustleX",
    language: "Language",
    profile: "Profile",
    name: "Name",
    contact: "Contact",
    age: "Age",
    edit: "Edit",
    updateProfile: "Update Profile",
    currentData: "Current Data",
    footerNote: "Data is stored locally on this device.",
    assistant: {
      title: "Assistant",
      typingPlaceholder: "Type a command... e.g., 'set language to Amharic'",
      hintsPrefix: "Try:",
      responses: {
        hello: "Hi! Your profile is synced from Telegram. You can switch languages.",
        langSet: (l) => `Language set to ${l}.`,
        unknown: "Sorry, I didn't understand. Try 'set language to Amharic'."
      }
    },
    placeholders: { name: "Your name", contact: "you@example.com", age: "18" },
    labelsPreview: { name: "Name:", contact: "Contact:", age: "Age:" },
    errors: {
      nameRequired: "Name is required",
      contactInvalid: "Enter a valid email address",
      ageInvalid: "Enter a valid age (0-120)"
    },
    toastSaved: "Profile updated"
  },
  am: {
    appTitle: "ሀስልኤክስ",
    language: "ቋንቋ",
    profile: "መገለጫ",
    name: "ስም",
    contact: "መገናኛ",
    age: "ዕድሜ",
    edit: "አርትዕ",
    updateProfile: "መገለጫ አዘምን",
    currentData: "ያለው መረጃ",
    footerNote: "መረጃዎ በዚህ መሣሪያ ላይ ብቻ ይቀመጣል።",
    assistant: {
      title: "አጋር",
      typingPlaceholder: "ትእዛዝ ጻፉ... ለምሳሌ፡ 'ስም አርትዕ'",
      hintsPrefix: "ይሞክሩ:",
      responses: {
        hello: "ሰላም! መገለጫ ለማርትዕ እና ቋንቋ ለመቀየር እረዳለሁ።",
        enabled: "እሺ፣ አሁን ማርትዕ ትችላለህ/ትችላለሽ።",
        updated: "ክዋኔ ተከናውኗል። መገለጫ ተቀመጠ።",
        langSet: (l) => `ቋንቋ ወደ ${l} ተቀይሯል።`,
        unknown: "ይቅርታ፣ አልገባኝም። 'ስም አርትዕ' ወይም 'መገለጫ አዘምን' ይሞክሩ።"
      }
    },
    placeholders: { name: "ስምዎ", contact: "you@example.com", age: "18" },
    labelsPreview: { name: "ስም:", contact: "መገናኛ:", age: "ዕድሜ:" },
    errors: {
      nameRequired: "ስም አስፈላጊ ነው",
      contactInvalid: "ትክክለኛ ኢሜይል ያስገቡ",
      ageInvalid: "ትክክለኛ ዕድሜ (0-120) ያስገቡ"
    },
    toastSaved: "መገለጫ ተቀመጠ"
  },
  om: {
    appTitle: "HustleX",
    language: "Afaan",
    profile: "Piroofaayilii",
    name: "Maqaa",
    contact: "Lakkoofsa quunnamtii/E-mail",
    age: "Umrii",
    edit: "Sirreessi",
    updateProfile: "Piroofaayilii fooyyessi",
    currentData: "Daataa ammaa",
    footerNote: "Daataan kun meeshaa kana irratti qofa ni kuufama.",
    assistant: {
      title: "Gargaaraa",
      typingPlaceholder: "Ajaja barreessi... fakkeenyaaf, 'maqaa sirreessi'",
      hintsPrefix: "Yaali:",
      responses: {
        hello: "Akkam! Piroofaayilii jijjiiru fi afaan baddaluu nan danda'a.",
        enabled: "Tole, amma ni sirreessita.",
        updated: "Raawwatame. Piroofaayilii ni kuufame.",
        langSet: (l) => `Afaan gara ${l}tti jijjiirame.`,
        unknown: "Dhiifama, hin hubadne. 'maqaa sirreessi' yookaan 'piroofaayilii fooyyessi' yaali."
      }
    },
    placeholders: { name: "Maqaa kee", contact: "you@example.com", age: "18" },
    labelsPreview: { name: "Maqaa:", contact: "Quunnamtii:", age: "Umrii:" },
    errors: {
      nameRequired: "Maqaan barbaachisa",
      contactInvalid: "Email sirrii galchi",
      ageInvalid: "Umrii (0-120) sirrii galchi"
    },
    toastSaved: "Piroofaayiliin ni haaromfame"
  }
};

const storageKeys = {
  profile: "hustlex.profile",
  lang: "hustlex.lang"
};

function getEl(id) { return document.getElementById(id); }

function loadProfile() {
  try { return JSON.parse(localStorage.getItem(storageKeys.profile)) || {}; }
  catch { return {}; }
}

function saveProfile(profile) {
  localStorage.setItem(storageKeys.profile, JSON.stringify(profile));
}

function loadLang() {
  const saved = localStorage.getItem(storageKeys.lang);
  if (saved && translations[saved]) return saved;
  return "en";
}

function saveLang(lang) {
  localStorage.setItem(storageKeys.lang, lang);
}

function validate(profile, t) {
  const errors = {};
  if (!profile.name || profile.name.trim().length === 0) errors.name = t.errors.nameRequired;
  const email = profile.contact || "";
  const emailOk = /.+@.+\..+/.test(email);
  if (email && !emailOk) errors.contact = t.errors.contactInvalid;
  const ageNum = Number(profile.age);
  if (Number.isNaN(ageNum) || ageNum < 0 || ageNum > 120) errors.age = t.errors.ageInvalid;
  return errors;
}

function applyLang(lang) {
  const t = translations[lang];
  if (!t) return;
  // Static labels
  getEl("appTitle").textContent = t.appTitle;
  getEl("languageLabel").textContent = t.language;
  getEl("profileTitle").textContent = t.profile;
  getEl("nameLabel").textContent = t.name;
  getEl("contactLabel").textContent = t.contact;
  getEl("previewTitle").textContent = t.currentData;
  // Assistant section
  const assistantTitle = getEl("assistantTitle");
  if (assistantTitle) assistantTitle.textContent = t.assistant?.title || "Assistant";
  const chatInput = getEl("chatInput");
  if (chatInput) chatInput.placeholder = t.assistant?.typingPlaceholder || chatInput.placeholder;
  const hints = document.getElementById("assistantHints");
  if (hints && t.assistant?.hintsPrefix) {
    hints.querySelector("span").textContent = t.assistant.hintsPrefix;
  }
  getEl("prevNameLabel").textContent = t.labelsPreview.name;
  getEl("prevContactLabel").textContent = t.labelsPreview.contact;
  getEl("prevAgeLabel").textContent = t.labelsPreview.age;
  getEl("footerNote").textContent = t.footerNote;

  // Placeholders
  getEl("nameInput").placeholder = t.placeholders.name;
  getEl("contactInput").placeholder = t.placeholders.contact;
  // Age removed from manual entry. No placeholder needed.
}

function setReadonly() {}

function renderPreview(profile) {
  getEl("prevName").textContent = profile.name || "—";
  getEl("prevContact").textContent = profile.contact || "—";
  getEl("prevAge").textContent = "—";
}

function clearErrors() {
  ["nameError","contactError","ageError"].forEach(id => { const el = getEl(id); if (el) el.textContent = ""; });
}

function showErrors(errors) {
  getEl("nameError").textContent = errors.name || "";
  getEl("contactError").textContent = errors.contact || "";
  getEl("ageError").textContent = errors.age || "";
}

function toast(message) {
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = message;
  Object.assign(el.style, {
    position: "fixed",
    bottom: "20px",
    right: "20px",
    background: "#121a33",
    color: "#e6ecff",
    border: "1px solid rgba(255,255,255,0.16)",
    padding: "10px 14px",
    borderRadius: "10px",
    boxShadow: "0 10px 20px rgba(0,0,0,0.25)",
    zIndex: 9999,
    opacity: 0,
    transition: "opacity 200ms ease"
  });
  document.body.appendChild(el);
  requestAnimationFrame(() => el.style.opacity = 1);
  setTimeout(() => {
    el.style.opacity = 0;
    setTimeout(() => el.remove(), 300);
  }, 1400);
}

// Init
document.addEventListener("DOMContentLoaded", () => {
  const langSelect = getEl("langSelect");
  const form = getEl("profileForm");

  const initialLang = loadLang();
  langSelect.value = initialLang;
  applyLang(initialLang);

  const savedProfile = loadProfile();
  const tg = window.Telegram?.WebApp;
  const unsafe = tg?.initDataUnsafe || {};
  const user = unsafe.user || {};
  const profileFromTelegram = {
    name: [user.first_name, user.last_name].filter(Boolean).join(" ") || "",
    contact: user.username ? `@${user.username}` : (user.phone_number || ""),
  };
  const profile = Object.assign({}, savedProfile, profileFromTelegram);
  getEl("nameInput").value = profile.name || "";
  getEl("contactInput").value = profile.contact || "";
  renderPreview(profile);
  saveProfile(profile);

  // Greet from assistant
  enqueueBot(translations[initialLang].assistant.responses.hello);

  // Language switching
  langSelect.addEventListener("change", () => {
    const lang = langSelect.value;
    if (!translations[lang]) return;
    saveLang(lang);
    applyLang(lang);
  });

  // No manual editing or form submission. Fields are inherited from Telegram.

  // Chat bot
  const chatForm = getEl("chatForm");
  const chatInput2 = getEl("chatInput");
  const chatLog = getEl("chatLog");

  function enqueueUser(text) {
    const div = document.createElement("div");
    div.className = "msg msg--user";
    div.textContent = text;
    chatLog.appendChild(div);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function enqueueBot(text) {
    const div = document.createElement("div");
    div.className = "msg msg--bot";
    div.textContent = text;
    chatLog.appendChild(div);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function handleCommand(raw) {
    const lang = loadLang();
    const t = translations[lang];
    const msg = raw.trim().toLowerCase();
    if (!msg) return;

    // Language commands
    if (/(set|change) (the )?language to (english|amharic|afaan oromo|oromo)/i.test(raw)) {
      const lower = raw.toLowerCase();
      const target = lower.includes("amharic") ? "am" : (lower.includes("oromo") ? "om" : "en");
      saveLang(target);
      getEl("langSelect").value = target;
      applyLang(target);
      const langName = target === "am" ? "Amharic" : target === "om" ? "Afaan Oromo" : "English";
      enqueueBot(translations[target].assistant.responses.langSet(langName));
      return;
    }

    // Edit name commands (multi-language)
    if (/(edit|change|update|sirreessi|አርትዕ).*name|ስም|maqaa/i.test(raw)) {
      const nameInput = getEl("nameInput");
      nameInput.removeAttribute("readonly");
      nameInput.focus();
      nameInput.style.borderColor = "#4f7cff";
      nameInput.style.backgroundColor = "rgba(79, 124, 255, 0.05)";
      enqueueBot(t.assistant.responses.enabled || "OK, you can now edit your name. Type the new value and press Enter.");
      
      // Set up one-time enter listener
      const updateName = (e) => {
        if (e.key === "Enter") {
          const newValue = nameInput.value.trim();
          if (newValue) {
            const profile = loadProfile();
            profile.name = newValue;
            saveProfile(profile);
            renderPreview(profile);
            enqueueBot(t.assistant.responses.updated || "Profile updated successfully.");
            nameInput.setAttribute("readonly", "true");
            nameInput.style.borderColor = "";
            nameInput.style.backgroundColor = "";
          }
          nameInput.removeEventListener("keydown", updateName);
        }
      };
      nameInput.addEventListener("keydown", updateName);
      return;
    }

    // Edit contact commands (multi-language)
    if (/(edit|change|update|sirreessi|አርትዕ).*(contact|email|phone|መገናኛ|quunnamtii)/i.test(raw)) {
      const contactInput = getEl("contactInput");
      contactInput.removeAttribute("readonly");
      contactInput.focus();
      contactInput.style.borderColor = "#4f7cff";
      contactInput.style.backgroundColor = "rgba(79, 124, 255, 0.05)";
      enqueueBot(t.assistant.responses.enabled || "OK, you can now edit your contact. Type the new value and press Enter.");
      
      // Set up one-time enter listener
      const updateContact = (e) => {
        if (e.key === "Enter") {
          const newValue = contactInput.value.trim();
          if (newValue) {
            const profile = loadProfile();
            profile.contact = newValue;
            saveProfile(profile);
            renderPreview(profile);
            enqueueBot(t.assistant.responses.updated || "Profile updated successfully.");
            contactInput.setAttribute("readonly", "true");
            contactInput.style.borderColor = "";
            contactInput.style.backgroundColor = "";
          }
          contactInput.removeEventListener("keydown", updateContact);
        }
      };
      contactInput.addEventListener("keydown", updateContact);
      return;
    }

    // Set name to value commands
    if (/(set|change).*(name|ስም|maqaa)\s+to\s+(.+)/i.test(raw)) {
      const match = raw.match(/(set|change).*(name|ስም|maqaa)\s+to\s+(.+)/i);
      if (match && match[3]) {
        const newName = match[3].trim();
        const profile = loadProfile();
        profile.name = newName;
        saveProfile(profile);
        getEl("nameInput").value = newName;
        renderPreview(profile);
        enqueueBot(t.assistant.responses.updated || "Profile updated successfully.");
        return;
      }
    }

    // Set contact to value commands
    if (/(set|change).*(contact|email|መገናኛ|quunnamtii)\s+to\s+(.+)/i.test(raw)) {
      const match = raw.match(/(set|change).*(contact|email|መገናኛ|quunnamtii)\s+to\s+(.+)/i);
      if (match && match[3]) {
        const newContact = match[3].trim();
        const profile = loadProfile();
        profile.contact = newContact;
        saveProfile(profile);
        getEl("contactInput").value = newContact;
        renderPreview(profile);
        enqueueBot(t.assistant.responses.updated || "Profile updated successfully.");
        return;
      }
    }

    // Hello/help commands
    if (/(hello|hi|help|selam|ሰላም|akkam)/i.test(msg)) {
      enqueueBot(t.assistant.responses.hello);
      return;
    }

    enqueueBot(t.assistant.responses.unknown);
  }

  chatForm?.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = chatInput2.value;
    enqueueUser(text);
    handleCommand(text);
    chatInput2.value = "";
  });
});

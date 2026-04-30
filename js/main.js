/* Small client-side behavior: theme toggle, mobile nav, copy email, contact form. */
(function () {
  const $ = (sel, root = document) => root.querySelector(sel);

  // ---------- Theme ----------
  const THEME_KEY = "bio_site_theme";
  const themeToggle = $('[data-theme-toggle]');
  const rootEl = document.documentElement;

  function getPreferredTheme() {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === "light" || stored === "dark") return stored;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function applyTheme(theme) {
    rootEl.dataset.theme = theme;
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      // Ignore storage errors (private mode etc.)
    }
  }

  applyTheme(getPreferredTheme());

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const next = rootEl.dataset.theme === "dark" ? "light" : "dark";
      applyTheme(next);
    });
  }

  // ---------- Mobile nav ----------
  const navToggle = $('[data-nav-toggle]');
  const navList = $('[data-nav-list]');

  function setNavOpen(open) {
    document.body.classList.toggle("nav-open", open);
    if (navToggle) navToggle.setAttribute("aria-expanded", String(open));
  }

  if (navToggle && navList) {
    navToggle.addEventListener("click", () => {
      const open = !document.body.classList.contains("nav-open");
      setNavOpen(open);
    });

    navList.addEventListener("click", (e) => {
      const target = e.target.closest("a");
      if (!target) return;
      setNavOpen(false);
    });
  }

  // ---------- Footer year ----------
  const yearEl = $("#year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  // ---------- Copy email ----------
  const copyBtn = $('[data-copy-email]');
  const emailDisplay = $('[data-email-display]');
  const contactStatus = $("#contactStatus");

  function setStatus(text) {
    if (!contactStatus) return;
    contactStatus.textContent = text;
    contactStatus.style.opacity = "1";
    window.clearTimeout(setStatus._t);
    setStatus._t = window.setTimeout(() => {
      if (contactStatus) contactStatus.textContent = "";
    }, 3500);
  }

  if (copyBtn && emailDisplay) {
    const email = String(emailDisplay.textContent || "").trim();
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(email);
        setStatus("Email clipboardga nusxalandi.");
      } catch {
        // Fallback (older browsers): try selecting via prompt
        window.prompt("Emailni nusxalang:", email);
      }
    });
  }

  // ---------- Contact form ----------
  const form = $("#contactForm");
  const clearBtn = $("#clearBtn");
  if (!form) return;

  const nameInput = $("#name");
  const emailInput = $("#email");
  const messageInput = $("#message");

  const fieldError = (fieldId) => $(`[data-error-for="${fieldId}"]`);

  function clearErrors() {
    ["name", "email", "message"].forEach((id) => {
      const el = fieldError(id);
      if (el) el.textContent = "";
    });
  }

  function isValidEmail(value) {
    // Simple email check, good enough for UI validation.
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || "").trim());
  }

  function validate() {
    clearErrors();

    const errors = {};
    const name = String(nameInput?.value || "").trim();
    const email = String(emailInput?.value || "").trim();
    const message = String(messageInput?.value || "").trim();

    if (!name) errors.name = "Ism kiritilishi shart.";
    if (!email) errors.email = "Email kiritilishi shart.";
    else if (!isValidEmail(email)) errors.email = "Email formati noto'g'ri.";
    if (!message) errors.message = "Xabar kiritilishi shart.";
    else if (message.length < 10) errors.message = "Xabar kamida 10 ta belgi bo'lsin.";

    for (const [k, v] of Object.entries(errors)) {
      const el = fieldError(k);
      if (el) el.textContent = v;
    }

    return Object.keys(errors).length === 0;
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    if (!validate()) {
      setStatus("Iltimos, xatolarni to'g'rilang.");
      return;
    }

    const name = String(nameInput.value || "").trim();
    const email = String(emailInput.value || "").trim();
    const message = String(messageInput.value || "").trim();
    const toEmail = emailDisplay ? String(emailDisplay.textContent || "").trim() : "you@example.com";

    const subject = encodeURIComponent(`Bio sayti bo'yicha xabar: ${name}`);
    const body = encodeURIComponent(
      `Ism: ${name}\nEmail: ${email}\n\nXabar:\n${message}\n`
    );

    // Open the user's mail client with a pre-filled message.
    setStatus("Email ochilyapti...");
    window.location.href = `mailto:${encodeURIComponent(toEmail)}?subject=${subject}&body=${body}`;
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      form.reset();
      clearErrors();
      setStatus("Forma tozalandi.");
    });
  }
})();


/* =========================================================
   auth.js — кнопка «Войти через VK ID» (OAuth 2.1 + PKCE)
   - Генерирует code_verifier и code_challenge (S256).
   - Редиректит на https://id.vk.ru/authorize.
   - Возвращается обратно на /oauth-callback.html.
   ========================================================= */

const VK_AUTH_CONFIG = {
  // Эти значения — публичные (видны в JS), это нормально для OAuth 2.1 PKCE.
  // Standalone ID_приложения из VK ID Cabinet (на модерации)
  clientId: "54654398",
  authorizeUrl: "https://id.vk.ru/authorize",
  redirectUri: window.location.origin + "/oauth-callback.html",
  // При подключении сообществ добавим: "groups wall photos"
  scope: "vkid.personal_info email",
  stateLength: 32,
  verifierLength: 64,
};

// ---------- Утилиты ----------

function base64url(bytes) {
  let bin = "";
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function randomString(byteLen) {
  const bytes = new Uint8Array(byteLen);
  crypto.getRandomValues(bytes);
  return base64url(bytes).replace(/[^A-Za-z0-9\-._~]/g, "A").slice(0, byteLen);
}

async function sha256(str) {
  const enc = new TextEncoder().encode(str);
  const buf = await crypto.subtle.digest("SHA-256", enc);
  return new Uint8Array(buf);
}

async function makePkcePair() {
  const verifier = randomString(VK_AUTH_CONFIG.verifierLength);
  const challenge = base64url(await sha256(verifier));
  return { verifier, challenge };
}

function randomState() {
  return randomString(VK_AUTH_CONFIG.stateLength);
}

// ---------- Главная функция: войти через VK ID ----------

async function startVkLogin() {
  const { verifier, challenge } = await makePkcePair();
  const state = randomState();
  const deviceId = randomString(16);

  sessionStorage.setItem("vk_oauth_verifier", verifier);
  sessionStorage.setItem("vk_oauth_state", state);
  sessionStorage.setItem("vk_oauth_device_id", deviceId);

  const url = new URL(VK_AUTH_CONFIG.authorizeUrl);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("client_id", VK_AUTH_CONFIG.clientId);
  url.searchParams.set("redirect_uri", VK_AUTH_CONFIG.redirectUri);
  url.searchParams.set("code_challenge", challenge);
  url.searchParams.set("code_challenge_method", "S256");
  url.searchParams.set("scope", VK_AUTH_CONFIG.scope);
  url.searchParams.set("state", state);
  url.searchParams.set("device_id", deviceId);
  url.searchParams.set("prompt", "select_account");

  window.location.assign(url.toString());
}

// ---------- Состояние «залогинен» на главной ----------

function isLoggedIn() {
  const token = sessionStorage.getItem("vk_access_token");
  const expStr = sessionStorage.getItem("vk_expires_at");
  if (!token) return false;
  const exp = parseInt(expStr || "0", 10);
  if (!exp || Date.now() > exp) return false;
  return true;
}

function logout() {
  sessionStorage.removeItem("vk_access_token");
  sessionStorage.removeItem("vk_user_id");
  sessionStorage.removeItem("vk_expires_at");
}

window.VKAuth = { startVkLogin, isLoggedIn, logout };

// ---------- Автопривязка кнопки ----------

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.querySelector("[data-vk-login]");
  if (btn) {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      startVkLogin();
    });
  }

  if (new URLSearchParams(window.location.search).get("vk_login") === "success" && isLoggedIn()) {
    const chip = document.querySelector(".vk-user-chip");
    if (chip) {
      const userId = sessionStorage.getItem("vk_user_id");
      chip.hidden = false;
      chip.textContent = "VK user_id: " + userId;
    }
  }
});
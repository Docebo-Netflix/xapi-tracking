<script>
// ================== CONFIG ==================
const HEARTBEAT_MS = 30000; // 30s
const RELAY = "https://xapi-tracking.onrender.com/track"; // <— REPLACE with your live /track URL
// ============================================

// DOM refs
const el = (id)=>document.getElementById(id);
const relayEl = el('relay');
const activityEl = el('activity');
const emailEl = el('email');
const nameEl = el('name');
const statusEl = el('status');
const startedAtEl = el('startedAt');
const nowEl = el('now');
const durEl = el('dur');
const logEl = el('log');

// State
let sessionStart = null;
let hbTimer = null;

// Helpers
const iso = (t)=> new Date(t).toISOString();
const log = (obj)=> {
  const line = typeof obj === 'string' ? obj : JSON.stringify(obj);
  const ts = new Date().toLocaleTimeString();
  logEl.textContent = `[${ts}] ${line}\n` + logEl.textContent;
};
const badge = (kind, text)=>{
  statusEl.className = `pill ${kind}`;
  statusEl.textContent = text;
};

async function send(eventType, extra={}) {
  const relayUrl = (relayEl.value || RELAY).trim();
  const payload = {
    eventType,
    userEmail: emailEl.value.trim(),
    userName:  nameEl.value.trim(),
    activityId: activityEl.value.trim(),
    ...extra
  };
  try {
    const res = await fetch(relayUrl, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
      keepalive: eventType === "terminated" // helps on pagehide
    });
    const body = await res.json().catch(()=> ({}));
    log({ sent: payload, status: res.status, ok: res.ok, body });
    return res.ok;
  } catch (e) {
    log({ error: String(e) });
    return false;
  }
}

function startSession() {
  if (sessionStart) return;
  sessionStart = Date.now();
  startedAtEl.textContent = iso(sessionStart);
  badge('ok','running');
  send("initialized");
  hbTimer = setInterval(()=> send("interacted"), HEARTBEAT_MS);
}

function stopSession() {
  if (!sessionStart) return;
  const dur = Math.round((Date.now() - sessionStart)/1000);
  send("terminated", { durationSec: dur });
  clearInterval(hbTimer); hbTimer = null;
  sessionStart = null;
  badge('warn','idle');
}

// Manual buttons
el('startBtn').addEventListener('click', startSession);
el('beatBtn').addEventListener('click', ()=> send("interacted"));
el('stopBtn').addEventListener('click', stopSession);

// Auto flow
window.addEventListener('load', startSession);
window.addEventListener('pagehide', stopSession);

// UI clock
setInterval(()=>{
  const t = Date.now();
  nowEl.textContent = iso(t);
  durEl.textContent = sessionStart ? Math.round((t - sessionStart)/1000) : 0;
}, 1000);
</script>
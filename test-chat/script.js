// ---------- Abas ----------
const tabButtons = document.querySelectorAll('.tab-btn');
const tabPanels = document.querySelectorAll('.tab-panel');

function goToTab(name) {
  tabButtons.forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  tabPanels.forEach(p => p.classList.toggle('active', p.id === `tab-${name}`));
}

tabButtons.forEach(btn => btn.addEventListener('click', () => goToTab(btn.dataset.tab)));
document.querySelectorAll('[data-goto]').forEach(btn =>
  btn.addEventListener('click', () => goToTab(btn.dataset.goto))
);

// ---------- Configuração (salva no localStorage do navegador) ----------
const els = {
  baseUrl: document.getElementById('cfg-base-url'),
  apiKey: document.getElementById('cfg-api-key'),
  model: document.getElementById('cfg-model'),
  stream: document.getElementById('cfg-stream'),
  status: document.getElementById('cfg-status'),
  saveBtn: document.getElementById('btn-save-cfg'),
  messages: document.getElementById('messages'),
  form: document.getElementById('chat-form'),
  input: document.getElementById('chat-input'),
  send: document.getElementById('chat-send'),
};

const STORAGE_KEY = 'orbit-ia-test-config';

function loadConfig() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    els.baseUrl.value = saved.baseUrl || '';
    els.apiKey.value = saved.apiKey || '';
    els.model.value = saved.model || '';
    els.stream.checked = saved.stream !== false;
    els.status.textContent = saved.baseUrl
      ? `Configuração carregada (${saved.baseUrl}).`
      : 'Nada salvo ainda.';
  } catch {
    els.status.textContent = 'Nada salvo ainda.';
  }
}

function saveConfig() {
  const cfg = {
    baseUrl: els.baseUrl.value.trim().replace(/\/+$/, ''),
    apiKey: els.apiKey.value.trim(),
    model: els.model.value.trim(),
    stream: els.stream.checked,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg));
  els.status.textContent = 'Configuração salva neste navegador ✓';
  return cfg;
}

els.saveBtn.addEventListener('click', saveConfig);
loadConfig();

// ---------- Chat ----------
let history = []; // {role, content}

function addBubble(role, text) {
  const wrap = document.createElement('div');
  wrap.className = `msg msg-${role}`;
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;
  wrap.appendChild(bubble);
  els.messages.appendChild(wrap);
  els.messages.scrollTop = els.messages.scrollHeight;
  return bubble;
}

function addThinking() {
  const wrap = document.createElement('div');
  wrap.className = 'msg msg-ai';
  wrap.id = 'thinking-bubble';
  wrap.innerHTML = `<div class="bubble"><span class="thinking"><span></span><span></span><span></span></span></div>`;
  els.messages.appendChild(wrap);
  els.messages.scrollTop = els.messages.scrollHeight;
}

function removeThinking() {
  document.getElementById('thinking-bubble')?.remove();
}

// Ajusta altura do textarea automaticamente
els.input.addEventListener('input', () => {
  els.input.style.height = 'auto';
  els.input.style.height = Math.min(els.input.scrollHeight, 140) + 'px';
});

els.form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = els.input.value.trim();
  if (!text) return;

  const cfg = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
  if (!cfg.baseUrl) {
    addBubble('error', 'Configure a URL base da API na barra lateral antes de testar.');
    return;
  }

  addBubble('user', text);
  history.push({ role: 'user', content: text });
  els.input.value = '';
  els.input.style.height = 'auto';
  els.send.disabled = true;
  addThinking();

  try {
    if (cfg.stream) {
      await streamChat(cfg);
    } else {
      await singleShotChat(cfg);
    }
  } catch (err) {
    removeThinking();
    addBubble('error', `Erro ao chamar a API: ${err.message}`);
  } finally {
    els.send.disabled = false;
  }
});

async function singleShotChat(cfg) {
  const res = await fetch(`${cfg.baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${cfg.apiKey}`,
    },
    body: JSON.stringify({
      model: cfg.model || 'llama3',
      messages: history,
      stream: false,
    }),
  });
  removeThinking();
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  const data = await res.json();
  const content = data.choices?.[0]?.message?.content ?? '(sem conteúdo)';
  addBubble('ai', content);
  history.push({ role: 'assistant', content });
}

async function streamChat(cfg) {
  const res = await fetch(`${cfg.baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${cfg.apiKey}`,
    },
    body: JSON.stringify({
      model: cfg.model || 'llama3',
      messages: history,
      stream: true,
    }),
  });

  if (!res.ok || !res.body) {
    removeThinking();
    throw new Error(`${res.status} ${await res.text()}`);
  }

  removeThinking();
  const bubble = addBubble('ai', '');
  let fullText = '';

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop(); // guarda linha incompleta

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith('data:')) continue;
      const payload = trimmed.slice(5).trim();
      if (payload === '[DONE]') continue;
      try {
        const json = JSON.parse(payload);
        const delta = json.choices?.[0]?.delta?.content;
        if (delta) {
          fullText += delta;
          bubble.textContent = fullText;
          els.messages.scrollTop = els.messages.scrollHeight;
        }
      } catch {
        // linha parcial ou não-JSON, ignora
      }
    }
  }

  history.push({ role: 'assistant', content: fullText });
}

// Enter envia, Shift+Enter quebra linha
els.input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    els.form.requestSubmit();
  }
});

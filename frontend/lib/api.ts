/**
 * Cliente da Orbit AI API.
 * Este é o ÚNICO módulo do frontend que faz chamadas HTTP para o backend.
 * O frontend NUNCA chama o provedor de IA diretamente — tudo passa por aqui,
 * que por sua vez fala com a API própria da Orbit IA.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("orbit_access_token");
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("orbit_refresh_token");
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("orbit_access_token", access);
  localStorage.setItem("orbit_refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("orbit_access_token");
  localStorage.removeItem("orbit_refresh_token");
}

async function request(path: string, options: RequestInit = {}): Promise<Response> {
  const token = getAccessToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (response.status === 401 && getRefreshToken()) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      headers.set("Authorization", `Bearer ${getAccessToken()}`);
      response = await fetch(`${API_URL}${path}`, { ...options, headers });
    }
  }
  return response;
}

async function tryRefreshToken(): Promise<boolean> {
  const refresh_token = getRefreshToken();
  if (!refresh_token) return false;
  const res = await fetch(`${API_URL}/api/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token }),
  });
  if (!res.ok) {
    clearTokens();
    return false;
  }
  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  return true;
}

export const orbitApi = {
  API_URL,

  async register(email: string, password: string, full_name?: string) {
    const res = await fetch(`${API_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Falha no cadastro");
    return res.json();
  },

  async login(email: string, password: string) {
    const res = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Falha no login");
    return res.json();
  },

  oauthUrl(provider: "google" | "github") {
    return `${API_URL}/api/auth/oauth/${provider}/login`;
  },

  async me() {
    const res = await request("/api/auth/me");
    if (!res.ok) throw new Error("Nao autenticado");
    return res.json();
  },

  async listConversations(q?: string) {
    const query = q ? `?q=${encodeURIComponent(q)}` : "";
    const res = await request(`/api/conversations${query}`);
    return res.json();
  },

  async getConversation(id: string) {
    const res = await request(`/api/conversations/${id}`);
    return res.json();
  },

  async renameConversation(id: string, title: string) {
    const res = await request(`/api/conversations/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    });
    return res.json();
  },

  async deleteConversation(id: string) {
    await request(`/api/conversations/${id}`, { method: "DELETE" });
  },

  exportUrl(id: string, format: "markdown" | "pdf") {
    return `${API_URL}/api/conversations/${id}/export?format=${format}`;
  },

  async uploadFile(file: File, conversationId?: string) {
    const formData = new FormData();
    formData.append("file", file);
    const query = conversationId ? `?conversation_id=${conversationId}` : "";
    const res = await request(`/api/files/upload${query}`, { method: "POST", body: formData });
    if (!res.ok) throw new Error((await res.json()).detail || "Falha no upload");
    return res.json();
  },

  async getMemory() {
    const res = await request("/api/memory");
    return res.json();
  },

  async setMemory(key: string, value: string) {
    const res = await request("/api/memory", { method: "POST", body: JSON.stringify({ key, value }) });
    return res.json();
  },

  async deleteMemory(key: string) {
    await request(`/api/memory/${encodeURIComponent(key)}`, { method: "DELETE" });
  },

  async updateProfile(payload: Record<string, unknown>) {
    const res = await request("/api/users/me", { method: "PATCH", body: JSON.stringify(payload) });
    return res.json();
  },

  async version() {
    const res = await fetch(`${API_URL}/api/version`);
    return res.json();
  },

  async adminUsers() {
    const res = await request("/api/admin/users");
    return res.json();
  },

  async adminUsageSummary(days = 30) {
    const res = await request(`/api/admin/usage/summary?days=${days}`);
    return res.json();
  },

  async adminPluginLogs() {
    const res = await request("/api/admin/logs/plugins");
    return res.json();
  },

  async adminToggleUser(id: string) {
    const res = await request(`/api/admin/users/${id}/toggle-active`, { method: "PATCH" });
    return res.json();
  },

  /**
   * Envia uma mensagem de chat e consome o stream SSE da Orbit AI API,
   * invocando os callbacks conforme os eventos chegam.
   */
  async streamChat(
    payload: { message: string; conversation_id?: string; model?: string; use_web_search?: boolean },
    handlers: {
      onConversation?: (id: string) => void;
      onStatus?: (message: string) => void;
      onDelta?: (content: string) => void;
      onToolStart?: (tool: string) => void;
      onToolResult?: (tool: string, result: unknown) => void;
      onDone?: (usage: unknown) => void;
      onError?: (message: string) => void;
    }
  ) {
    const token = getAccessToken();
    const res = await fetch(`${API_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok || !res.body) {
      handlers.onError?.("Nao foi possivel conectar a Orbit IA.");
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;
        const jsonStr = line.slice(5).trim();
        try {
          const event = JSON.parse(jsonStr);
          switch (event.type) {
            case "conversation":
              handlers.onConversation?.(event.conversation_id);
              break;
            case "status":
              handlers.onStatus?.(event.message);
              break;
            case "delta":
              handlers.onDelta?.(event.content);
              break;
            case "tool_start":
              handlers.onToolStart?.(event.tool);
              break;
            case "tool_result":
              handlers.onToolResult?.(event.tool, event.result);
              break;
            case "done":
              handlers.onDone?.(event.usage);
              break;
            case "error":
              handlers.onError?.(event.message);
              break;
          }
        } catch {
          // ignora linhas parciais nao parseaveis
        }
      }
    }
  },
};

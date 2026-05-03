const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const data = await response.json();
      message = data.detail || data.message || message;
    } catch {
      // Ignore JSON parsing errors and keep fallback message.
    }

    throw new Error(message);
  }

  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return null;
  }

  return response.json();
}

export function listSources() {
  return request("/api/v1/sources/");
}

export function getSource(sourceId) {
  return request(`/api/v1/sources/${sourceId}`);
}

export function createSource(payload) {
  return request("/api/v1/sources", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function refreshSource(sourceId) {
  return request(`/api/v1/sources/${sourceId}/refresh`, {
    method: "POST",
  });
}

export function listPages(sourceId) {
  return request(`/api/v1/pages/${sourceId}/`);
}

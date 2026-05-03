export function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatPercent(value) {
  return `${value.toFixed(1)}%`;
}

export function getSourceStatusTone(status) {
  if (status === "READY") {
    return "success";
  }
  if (status === "FAILED") {
    return "danger";
  }
  if (status === "CRAWLING" || status === "PROCESSING" || status === "REFRESHING") {
    return "accent";
  }
  return "muted";
}

export function getSourceStatusLabel(status) {
  if (status === "READY") {
    return "Synced";
  }
  if (status === "CRAWLING") {
    return "Crawling";
  }
  if (status === "PROCESSING") {
    return "Processing";
  }
  if (status === "REFRESHING") {
    return "Refreshing";
  }
  if (status === "FAILED") {
    return "Failed";
  }
  return status || "Unknown";
}

export function getPageStatusLabel(status) {
  if (status === "INDEXED") {
    return "Indexed";
  }
  if (status === "FAILED") {
    return "Failed";
  }
  return "Crawling";
}

export function getPathLabel(page) {
  if (page.url) {
    try {
      const url = new URL(page.url);
      return url.pathname || "/";
    } catch {
      return page.url;
    }
  }

  return page.title || "Untitled page";
}

export function getSourceTypeBadge(sourceType) {
  if (sourceType === "URL") {
    return "URL";
  }
  if (sourceType === "FILE") {
    return "FILE";
  }
  if (sourceType === "COLLECTION") {
    return "COLLECTION";
  }
  return sourceType;
}

const KNOWN_SYNC_FREQUENCIES = ["realtime", "hourly", "daily", "weekly", "manual"];

export function getSourceConfig(config) {
  return config && typeof config === "object" ? config : {};
}

export function getSyncFrequencyLabel(value) {
  const labels = {
    realtime: "Realtime",
    hourly: "Hourly",
    daily: "Daily",
    weekly: "Weekly",
    manual: "Manual only",
  };
  return labels[value] || "Hourly";
}

export function getAuthModeLabel(value) {
  const labels = {
    none: "No authentication",
    bearer: "Bearer token",
    basic: "Basic auth",
    api_key: "API key",
  };
  return labels[value] || "No authentication";
}

export function parseConfigForForm(config) {
  const safeConfig = getSourceConfig(config);
  const auth = safeConfig.auth && typeof safeConfig.auth === "object" ? safeConfig.auth : {};
  const extraConfig = { ...safeConfig };

  delete extraConfig.sync_frequency;
  delete extraConfig.auth;
  delete extraConfig.crawl_subdomains;
  delete extraConfig.exclusion_patterns;

  return {
    syncFrequency: KNOWN_SYNC_FREQUENCIES.includes(safeConfig.sync_frequency)
      ? safeConfig.sync_frequency
      : "hourly",
    authMode: typeof auth.mode === "string" ? auth.mode : "none",
    authToken:
      typeof auth.bearer_token === "string"
        ? auth.bearer_token
        : typeof auth.token === "string"
          ? auth.token
          : "",
    crawlSubdomains: Boolean(safeConfig.crawl_subdomains),
    exclusionPatterns: Array.isArray(safeConfig.exclusion_patterns)
      ? safeConfig.exclusion_patterns.join("\n")
      : "",
    advancedJson: JSON.stringify(extraConfig, null, 2),
  };
}

export function buildSourceConfig(form) {
  let extraConfig = {};

  try {
    extraConfig = form.advancedJson.trim() ? JSON.parse(form.advancedJson) : {};
  } catch {
    throw new Error("Advanced JSON config must be valid JSON.");
  }

  if (!extraConfig || typeof extraConfig !== "object" || Array.isArray(extraConfig)) {
    throw new Error("Advanced JSON config must be a JSON object.");
  }

  const exclusionPatterns = form.exclusionPatterns
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);

  const auth =
    form.authMode === "bearer"
      ? {
          mode: "bearer",
          bearer_token: form.authToken.trim(),
        }
      : {
          mode: form.authMode,
        };

  return {
    ...extraConfig,
    sync_frequency: form.syncFrequency,
    auth,
    crawl_subdomains: Boolean(form.crawlSubdomains),
    exclusion_patterns: exclusionPatterns,
  };
}

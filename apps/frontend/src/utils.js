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

export const navItems = [
  { id: "dashboard", label: "Dashboard", icon: "dashboard" },
  { id: "sources", label: "Sources", icon: "database" },
  { id: "logs", label: "Activity Logs", icon: "terminal" },
  { id: "settings", label: "Settings", icon: "settings" },
];

export const supportItems = [
  { id: "support", label: "Support", icon: "contact_support" },
  { id: "docs", label: "Documentation", icon: "menu_book" },
];

export const dashboardStats = [
  {
    label: "Total Sources",
    value: "24",
    meta: "+2 since last login",
    icon: "database",
    tone: "success",
  },
  {
    label: "Total Pages Indexed",
    value: "12,842",
    meta: "Last indexed 4m ago",
    icon: "description",
  },
  {
    label: "Embedding Status",
    value: "99.8%",
    meta: "Optimal",
    icon: "neurology",
    tone: "accent",
  },
  {
    label: "Sync Errors",
    value: "0",
    meta: "Healthy pipeline",
    icon: "error",
    tone: "danger",
  },
];

export const activeSources = [
  {
    name: "Engineering Wiki (Notion)",
    endpoint: "notion.so/org-id/6274-ad7...",
    type: "NOTION",
    meta: "1,402 DOCS",
    status: "Synced 12m ago",
    statusTone: "success",
    icon: "description",
    iconTone: "blue",
  },
  {
    name: "Core API Documentation",
    endpoint: "github.com/mcp-org/core-docs",
    type: "GITHUB",
    meta: "4.2MB TEXT",
    status: "Synced 1h ago",
    statusTone: "muted",
    icon: "data_object",
    iconTone: "orange",
  },
  {
    name: "Zendesk Help Center",
    endpoint: "support.docs-mcp.com/hc/en-us",
    type: "SYNCING",
    meta: "65%",
    status: "Crawling nodes...",
    statusTone: "accent",
    icon: "cloud_sync",
    iconTone: "blue",
    progress: 65,
  },
];

export const pipelineLogs = [
  ["14:22:01", "INFO", 'Starting index task for "Engineering Wiki"'],
  ["14:22:04", "INFO", "Fetched 1,402 items from Notion API"],
  ["14:22:15", "SUCCESS", "Embeddings generated for batch #14"],
  ["14:23:44", "WARN", "Retrying connection to GitHub API..."],
  ["14:23:50", "INFO", "GitHub connection re-established"],
  ["14:24:02", "INFO", "Zendesk crawler detected 44 new nodes"],
  ["14:24:10", "INFO", "_"],
];

export const pipelineSteps = [
  { label: "Ingestion", icon: "cloud_download", active: true },
  { label: "Cleaning", icon: "cleaning_services" },
  { label: "Embeddings", icon: "neurology", current: true },
  { label: "Vector Store", icon: "storage" },
];

export const sourceMetrics = [
  {
    label: "Total Pages",
    value: "1,284",
    meta: "+12% vs last sync",
    icon: "description",
    tone: "accent",
  },
  {
    label: "Sync Status",
    value: "Healthy",
    meta: "Last sync 4m ago",
    icon: "check_circle",
    tone: "success",
  },
  {
    label: "Tokens Used",
    value: "4.2M",
    meta: "Quota: 10M / month",
    icon: "memory",
    tone: "warm",
  },
  {
    label: "Crawl Speed",
    value: "82 p/s",
    meta: "Optimization: High",
    icon: "speed",
    tone: "info",
  },
];

export const indexedPages = [
  ["/docs/installation", "Indexed", "42 chunks"],
  ["/docs/utility-first", "Indexed", "18 chunks"],
  ["/docs/hover-focus-and-other-states", "Crawling", "--"],
  ["/docs/responsive-design", "Indexed", "31 chunks"],
];

export const detailLogs = [
  ["09:42:01", "INFO", "Initiating worker_02 sync for /docs/layout"],
  ["09:42:03", "INFO", "Vectorized 12 chunks successfully"],
  ["09:42:10", "INFO", "Skipping /blog/tailwind-v4-preview (Excluded)"],
  ["09:43:45", "BUSY", "Indexing /docs/flexbox-and-grid..."],
  ["09:44:12", "", "_"],
];

export const readinessChecks = [
  ["check_circle", "success", "Network Gateway", "Secure tunnel active (Port 443)"],
  ["check_circle", "success", "Worker Node Availability", "4 healthy nodes ready for indexing"],
  ["info", "accent", "Memory Pressure", "Optimal (12% usage)"],
];

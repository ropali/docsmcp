import { useEffect, useMemo, useState } from "react";
import { getSource, listPages, refreshSource } from "../api";
import Icon from "../components/Icon";
import LogPanel from "../components/LogPanel";
import StatCard from "../components/StatCard";
import { detailLogs } from "../data/mockData";
import {
  formatNumber,
  getAuthModeLabel,
  getPageStatusLabel,
  getPathLabel,
  getSourceConfig,
  getSourceStatusLabel,
  getSourceStatusTone,
  getSyncFrequencyLabel,
} from "../utils";

export default function SourceDetailScreen({ sourceId, reloadToken, onRefresh, onSourceLoaded, onEditSource }) {
  const [source, setSource] = useState(null);
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      if (!sourceId) {
        setSource(null);
        setPages([]);
        setLoading(false);
        return;
      }

      setLoading(true);
      setError("");

      try {
        const [sourceRow, pageRows] = await Promise.all([
          getSource(sourceId),
          listPages(sourceId),
        ]);

        if (!cancelled) {
          setSource(sourceRow);
          setPages(pageRows);
          onSourceLoaded(sourceRow);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadData();

    return () => {
      cancelled = true;
    };
  }, [sourceId, reloadToken]);

  const metrics = useMemo(() => {
    const indexedCount = pages.filter((page) => page.status === "INDEXED").length;
    const failedCount = pages.filter((page) => page.status === "FAILED").length;
    const totalChunks = pages.reduce((total, page) => total + (page.chunk_count || 0), 0);

    return [
      {
        label: "Total Pages",
        value: formatNumber(pages.length),
        meta: `${indexedCount} indexed / ${failedCount} failed`,
        icon: "description",
        tone: "accent",
      },
      {
        label: "Sync Status",
        value: source ? getSourceStatusLabel(source.status) : "Unknown",
        meta: source ? `State: ${source.status}` : "No source selected",
        icon: "check_circle",
        tone: source ? getSourceStatusTone(source.status) : "muted",
      },
      {
        label: "Chunks Indexed",
        value: formatNumber(totalChunks),
        meta: "Derived from page chunk counts",
        icon: "memory",
        tone: "warm",
      },
      {
        label: "Active Pages",
        value: formatNumber(pages.filter((page) => page.status !== "FAILED").length),
        meta: source?.base_url || "Unavailable",
        icon: "speed",
        tone: "info",
      },
    ];
  }, [pages, source]);

  const sourceConfig = useMemo(() => getSourceConfig(source?.config), [source?.config]);
  const extraConfig = useMemo(() => {
    const rest = { ...sourceConfig };
    delete rest.sync_frequency;
    delete rest.auth;
    delete rest.crawl_subdomains;
    delete rest.exclusion_patterns;
    return rest;
  }, [sourceConfig]);

  return (
    <>
      <section className="detailHero sourceViewHero">
        <div className="detailHeroTop">
          <div className="detailIntro">
            <div className="heroMeta">
              <span className="heroBadge active">Active Source</span>
              <span className="heroId">ID: {sourceId || "unavailable"}</span>
            </div>
            <h2 className="pageTitle">{source?.name || "Select a source"}</h2>
            <p className="pageDescription">
              {source?.base_url ||
                "Choose a source from the dashboard to inspect indexed pages and current crawl state."}
            </p>
          </div>

          <div className="headerActions">
            <button
              type="button"
              className="secondaryButton"
              disabled={!sourceId}
              onClick={async () => {
                if (!sourceId) {
                  return;
                }
                await refreshSource(sourceId);
                onRefresh();
              }}
            >
              <Icon name="refresh" />
              <span>Re-index</span>
            </button>
            <button
              type="button"
              className="primaryButton"
              disabled={!sourceId}
              onClick={() => {
                if (!sourceId || !source) {
                  return;
                }
                onEditSource(sourceId, source.name);
              }}
            >
              <Icon name="edit" />
              <span>Edit Source</span>
            </button>
          </div>
        </div>

        <div className="statsGrid fourUp">
          {metrics.map((metric) => (
            <StatCard key={metric.label} {...metric} />
          ))}
        </div>
      </section>

      <section className="detailGrid">
        <div className="detailMain">
          <article className="tableCard">
            <div className="tableHeader">
              <h3>Indexed Pages</h3>
              <div className="tableTools">
                <div className="searchWrap compact">
                  <Icon name="search" className="searchIcon" />
                  <input className="searchInput compact" placeholder="Filter pages..." type="text" />
                </div>
                <button type="button" className="iconButton subtleIcon">
                  <Icon name="filter_list" />
                </button>
              </div>
            </div>

            <div className="tableWrap">
              <table>
                <thead>
                  <tr>
                    <th>Page Path</th>
                    <th>Status</th>
                    <th>Vectors</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="4" className="emptyCell">Loading pages...</td>
                    </tr>
                  ) : null}
                  {!loading && error ? (
                    <tr>
                      <td colSpan="4" className="emptyCell">{error}</td>
                    </tr>
                  ) : null}
                  {!loading && !error && pages.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="emptyCell">No indexed pages available for this source.</td>
                    </tr>
                  ) : null}
                  {!loading && !error
                    ? pages.map((page) => (
                    <tr key={page.id}>
                      <td className="codeLink">{getPathLabel(page)}</td>
                      <td>
                        <span
                          className={`badge ${
                            page.status === "INDEXED"
                              ? "green"
                              : page.status === "FAILED"
                                ? "red"
                                : "blue"
                          }`}
                        >
                          {getPageStatusLabel(page.status)}
                        </span>
                      </td>
                      <td className="mutedCode">
                        {page.chunk_count ? `${page.chunk_count} chunks` : "--"}
                      </td>
                      <td>
                        <button type="button" className="iconButton subtleIcon">
                          <Icon name="more_vert" />
                        </button>
                      </td>
                    </tr>
                  ))
                    : null}
                </tbody>
              </table>
            </div>

            <div className="tableFooter">
              <span>Showing {pages.length} page{pages.length === 1 ? "" : "s"}</span>
              <div className="pagination">
                <button type="button" className="iconButton subtleIcon" disabled>
                  <Icon name="chevron_left" />
                </button>
                <button type="button" className="iconButton subtleIcon">
                  <Icon name="chevron_right" />
                </button>
              </div>
            </div>
          </article>
        </div>

        <aside className="detailSide">
          <article className="panelCard sourceConfigCard">
            <div className="panelHeading">
              <Icon name="settings_suggest" className="accentIcon" />
              <h3>Sync Configuration</h3>
            </div>

            <div className="configStack">
              <label className="field">
                <span>Sync Frequency</span>
                <div className="readOnlyValue">{getSyncFrequencyLabel(sourceConfig.sync_frequency)}</div>
              </label>

              <label className="field">
                <span>Authentication</span>
                <div className="readOnlyValue">
                  {getAuthModeLabel(sourceConfig.auth?.mode)}
                  {sourceConfig.auth?.mode === "bearer" && sourceConfig.auth?.bearer_token
                    ? " configured"
                    : ""}
                </div>
              </label>

              <div className="field">
                <span>Exclusion Patterns</span>
                <div className="codeBlock">
                  {Array.isArray(sourceConfig.exclusion_patterns) && sourceConfig.exclusion_patterns.length > 0
                    ? sourceConfig.exclusion_patterns.join("\n")
                    : "No exclusion patterns configured."}
                </div>
              </div>

              <label className="toggleRow">
                <span className={`toggle ${sourceConfig.crawl_subdomains ? "active" : ""}`}>
                  <span className="toggleKnob" />
                </span>
                <span>{sourceConfig.crawl_subdomains ? "Crawl subdomains enabled" : "Crawl subdomains disabled"}</span>
              </label>

              <div className="field">
                <span>Advanced Config JSON</span>
                <div className="codeBlock">
                  {Object.keys(extraConfig).length > 0
                    ? JSON.stringify(extraConfig, null, 2)
                    : "{}"}
                </div>
              </div>
            </div>
          </article>

          <LogPanel title="system_logs.sh" status="Live Connection" rows={detailLogs} compact />
        </aside>
      </section>

      <button type="button" className="fab">
        <Icon name="bolt" className="fabIcon" />
      </button>
    </>
  );
}

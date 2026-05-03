import { useEffect, useMemo, useState } from "react";
import { listPages, listSources, refreshSource } from "../api";
import { pipelineLogs, pipelineSteps } from "../data/mockData";
import StatCard from "../components/StatCard";
import SourceCard from "../components/SourceCard";
import LogPanel from "../components/LogPanel";
import Icon from "../components/Icon";
import {
  formatNumber,
  formatPercent,
  getSourceStatusLabel,
  getSourceStatusTone,
  getSourceTypeBadge,
} from "../utils";

export default function SourcesDashboard({ onNavigate, onSelectSource, onEditSource, reloadToken }) {
  const [sources, setSources] = useState([]);
  const [sourcePages, setSourcePages] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [localReloadToken, setLocalReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      setLoading(true);
      setError("");

      try {
        const sourceRows = await listSources();
        const pageEntries = await Promise.all(
          sourceRows.map(async (source) => [source.id, await listPages(source.id)]),
        );

        if (!cancelled) {
          setSources(sourceRows);
          setSourcePages(Object.fromEntries(pageEntries));
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
  }, [reloadToken, localReloadToken]);

  const stats = useMemo(() => {
    const allPages = Object.values(sourcePages).flat();
    const indexedPages = allPages.filter((page) => page.status === "INDEXED").length;
    const failedPages = allPages.filter((page) => page.status === "FAILED").length;
    const totalPages = allPages.length;
    const embeddingRate = totalPages > 0 ? (indexedPages / totalPages) * 100 : 0;

    return [
      {
        label: "Total Sources",
        value: formatNumber(sources.length),
        meta: `${sources.filter((source) => source.status === "READY").length} ready`,
        icon: "database",
        tone: "success",
      },
      {
        label: "Total Pages Indexed",
        value: formatNumber(totalPages),
        meta: `${indexedPages} indexed pages`,
        icon: "description",
      },
      {
        label: "Embedding Status",
        value: totalPages ? formatPercent(embeddingRate) : "0.0%",
        meta: totalPages ? `${indexedPages}/${totalPages} indexed` : "No pages available",
        icon: "neurology",
        tone: "accent",
      },
      {
        label: "Sync Errors",
        value: formatNumber(failedPages),
        meta: failedPages ? "Pages need reprocessing" : "Healthy pipeline",
        icon: "error",
        tone: failedPages ? "danger" : "success",
      },
    ];
  }, [sourcePages, sources]);

  const cards = useMemo(() => {
    return sources.map((source) => {
      const pages = sourcePages[source.id] || [];
      return {
        id: source.id,
        name: source.name,
        endpoint: source.base_url,
        type: getSourceTypeBadge(source.source_type),
        meta: `${formatNumber(pages.length)} DOCS`,
        status: getSourceStatusLabel(source.status),
        statusTone: getSourceStatusTone(source.status),
        icon: source.source_type === "URL" ? "description" : "data_object",
        iconTone: source.source_type === "URL" ? "blue" : "orange",
        progress: source.status === "CRAWLING" ? 65 : undefined,
      };
    });
  }, [sourcePages, sources]);

  return (
    <>
      <section className="pageHeader">
        <div>
          <div className="eyebrowLine">Workspace / Documentation</div>
          <h2 className="pageTitle">Sources Dashboard</h2>
          <p className="pageDescription dashboardDescription">
            Track source health, indexing coverage, and ingestion activity from one place.
          </p>
        </div>
        <div className="headerActions">
          <button type="button" className="primaryButton" onClick={() => onNavigate("add-source")}>
            <Icon name="add" />
            <span>Add Source</span>
          </button>
          <button type="button" className="secondaryButton">
            <Icon name="refresh" />
            <span>Re-index All</span>
          </button>
        </div>
      </section>

      <section className="statsGrid fourUp dashboardStats">
        {stats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </section>

      <section className="dashboardGrid">
        <div className="dashboardMain">
          <div className="sectionHeader">
            <div className="dashboardSectionIntro">
              <h3>Active Sources</h3>
              <p className="dashboardSectionMeta">
                {loading ? "Refreshing source inventory..." : `${formatNumber(cards.length)} sources currently connected`}
              </p>
            </div>
            <div className="viewToggle">
              <button type="button" className="iconButton subtleIcon">
                <Icon name="grid_view" />
              </button>
              <button type="button" className="iconButton darkIcon">
                <Icon name="list" />
              </button>
            </div>
          </div>

          <div className="stack sourceCardGrid">
            {loading ? <div className="inlineNotice">Loading sources...</div> : null}
            {error ? <div className="inlineNotice errorNotice">{error}</div> : null}
            {!loading && !error && cards.length === 0 ? (
              <div className="inlineNotice">No sources found. Create one to start indexing.</div>
            ) : null}
            {!loading && !error
              ? cards.map((source) => (
                  <SourceCard
                    key={source.id}
                    source={source}
                    onOpenDetail={() => onSelectSource(source.id, source.name)}
                    onEdit={() => onEditSource(source.id, source.name)}
                    onRefresh={async () => {
                      await refreshSource(source.id);
                      setLocalReloadToken((current) => current + 1);
                    }}
                  />
                ))
              : null}
          </div>
        </div>

        <div className="dashboardSide">
          <LogPanel title="Pipeline Logs" status="AUTO-SCROLL ON" rows={pipelineLogs} />
        </div>
      </section>

      <section className="pipelineCard">
        <div className="sectionHeader">
          <div className="dashboardSectionIntro">
            <h3 className="withIcon">
              <Icon name="account_tree" className="accentIcon" />
              <span>Data Pipeline Flow</span>
            </h3>
            <p className="dashboardSectionMeta">Current ingestion stages from source fetch to vector storage.</p>
          </div>
        </div>
        <div className="pipelineFlow">
          {pipelineSteps.map((step) => (
            <div key={step.label} className={`pipelineStep ${step.active ? "active" : ""} ${step.current ? "current" : ""}`}>
              <div className="pipelineNode">
                <Icon name={step.icon} className={step.current ? "pulse" : ""} fill={step.current} />
              </div>
              <span className="pipelineLabel">{step.label}</span>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

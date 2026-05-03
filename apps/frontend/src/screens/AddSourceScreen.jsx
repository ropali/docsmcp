import { useEffect, useMemo, useState } from "react";
import { createSource, getSource, updateSource } from "../api";
import Icon from "../components/Icon";
import { readinessChecks, pipelineLogs } from "../data/mockData";
import { buildSourceConfig, parseConfigForForm } from "../utils";

const protocolOptions = [
  { label: "HTTPS / REST API", value: "URL" },
  { label: "GraphQL", value: "URL" },
  { label: "Local Filesystem", value: "UNSUPPORTED" },
  { label: "Git Repository", value: "UNSUPPORTED" },
];



const emptyForm = {
  name: "",
  source_type: "URL",
  base_url: "",
  protocol: "HTTPS / REST API",
  crawlSubdomains: false,
  exclusionPatterns: "",
  advancedJson: "{}",
};

function getProtocolLabel(sourceType) {
  if (sourceType === "URL") {
    return "HTTPS / REST API";
  }
  return "HTTPS / REST API";
}

export default function AddSourceScreen({ sourceId = null, onSourceCreated, onSourceUpdated }) {
  const [form, setForm] = useState(emptyForm);
  const [loadingSource, setLoadingSource] = useState(Boolean(sourceId));
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const isEditing = Boolean(sourceId);

  const selectedProtocol = useMemo(
    () => protocolOptions.find((option) => option.label === form.protocol) || protocolOptions[0],
    [form.protocol],
  );

  useEffect(() => {
    let cancelled = false;

    async function loadSource() {
      if (!sourceId) {
        setForm(emptyForm);
        setLoadingSource(false);
        return;
      }

      setLoadingSource(true);
      setMessage("");
      setError("");

      try {
        const source = await getSource(sourceId);
        if (!cancelled) {
          const parsedConfig = parseConfigForForm(source.config);
          setForm({
            name: source.name || "",
            source_type: source.source_type || "URL",
            base_url: source.base_url || "",
            protocol: getProtocolLabel(source.source_type),
            ...parsedConfig,
          });
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError.message);
        }
      } finally {
        if (!cancelled) {
          setLoadingSource(false);
        }
      }
    }

    loadSource();

    return () => {
      cancelled = true;
    };
  }, [sourceId]);

  return (
    <>
      <section className="pageHeader narrow addSourceHeader">
        <div>
          <div className="breadcrumbs">
            <span>Sources</span>
            <Icon name="chevron_right" className="tinyIcon" />
            <span className="current">{isEditing ? "Edit Connection" : "New Connection"}</span>
          </div>
          <h2 className="pageTitle">{isEditing ? "Edit Source" : "Add New Source"}</h2>
          <p className="pageDescription">
            {isEditing
              ? "Update the source endpoint and operational config used by the DocsMCP ingestion pipeline."
              : "Connect a new external knowledge base, API endpoint, or local documentation directory to the DocsMCP index for real-time semantic search and context injection."}
          </p>
        </div>
      </section>

      <section className="addSourceGrid addSourceView">
        <div className="formColumn">
          <article className="panelCard largePanel addSourcePanel">
            <div className="panelHeading">
              <Icon name="cloud_sync" className="accentIcon" fill />
              <h3>Source Configuration</h3>
            </div>

            <form
              className="sourceForm"
              onSubmit={async (event) => {
                event.preventDefault();
                setMessage("");
                setError("");

                if (loadingSource) {
                  return;
                }

                if (selectedProtocol.value === "UNSUPPORTED") {
                  setError("This protocol is not supported by the current backend APIs.");
                  return;
                }



                let config;
                try {
                  config = buildSourceConfig(form);
                  // Remove auth and sync frequency options from create/edit payload
                  // These are managed by the backend or defaults and should not be set from the form
                  delete config.sync_frequency;
                  delete config.auth;
                } catch (configError) {
                  setError(configError.message);
                  return;
                }

                setSubmitting(true);
                try {
                  const response = isEditing
                    ? await updateSource(sourceId, {
                        name: form.name,
                        base_url: form.base_url,
                        config,
                      })
                    : await createSource({
                        name: form.name,
                        source_type: selectedProtocol.value,
                        base_url: form.base_url,
                        config,
                      });
                  setMessage(response.message || (isEditing ? "Source updated." : "Source created."));
                  if (response?.data?.id) {
                    if (isEditing) {
                      onSourceUpdated?.(response.data.id, response.data.name);
                    } else {
                      onSourceCreated?.(response.data.id, response.data.name);
                    }
                  }
                } catch (submitError) {
                  setError(submitError.message);
                } finally {
                  setSubmitting(false);
                }
              }}
            >
              <div className="formGrid">
                <label className="field">
                  <span>Source Name</span>
                  <input
                    disabled={loadingSource}
                    placeholder="e.g., AWS SDK Documentation"
                    type="text"
                    value={form.name}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, name: event.target.value }))
                    }
                  />
                </label>
                <label className="field">
                  <span>Protocol</span>
                  <select
                    disabled={isEditing}
                    value={form.protocol}
                    onChange={(event) => {
                      const option = protocolOptions.find(
                        (item) => item.label === event.target.value,
                      );
                      setForm((current) => ({
                        ...current,
                        protocol: option?.label || "HTTPS / REST API",
                        source_type: option?.value || "URL",
                      }));
                    }}
                  >
                    {protocolOptions.map((option) => (
                      <option key={option.label}>{option.label}</option>
                    ))}
                  </select>
                </label>
              </div>

              <label className="field">
                <span>Endpoint URL / Root Path</span>
                <div className="fieldIconWrap">
                  <Icon name="link" className="fieldIcon" />
                  <input
                    disabled={loadingSource}
                    placeholder="https://docs.api.example.com/v1"
                    type="url"
                    value={form.base_url}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, base_url: event.target.value }))
                    }
                  />
                </div>
              </label>





              <div className="formGrid">
                <label className="field">
                  <span>Exclusion Patterns</span>
                  <textarea
                    className="configTextarea"
                    disabled={loadingSource}
                    placeholder={"/blog/*\n/v1/*\n/deprecated/*"}
                    rows={5}
                    value={form.exclusionPatterns}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        exclusionPatterns: event.target.value,
                      }))
                    }
                  />
                </label>

                <div className="field">
                  <span>Crawl Scope</span>
                  <label className="toggleRow interactiveToggle">
                    <input
                      checked={form.crawlSubdomains}
                      disabled={loadingSource}
                      type="checkbox"
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          crawlSubdomains: event.target.checked,
                        }))
                      }
                    />
                    <span className={`toggle ${form.crawlSubdomains ? "active" : ""}`}>
                      <span className="toggleKnob" />
                    </span>
                    <span>Crawl subdomains</span>
                  </label>
                </div>
              </div>

              <article className="collapseCard advancedSettingsCard staticCard">
                <div className="collapseHead">
                  <div className="inlineGroup">
                    <Icon name="settings_input_component" />
                    <span>Advanced Config JSON</span>
                  </div>
                </div>
                <p className="configHelpText">
                  Provide additional JSON config for extraction, schema mapping, or source-specific crawler options. Structured fields above always override conflicting keys.
                </p>
                <label className="field">
                  <span>Extra Config</span>
                  <textarea
                    className="configTextarea codeTextarea"
                    disabled={loadingSource}
                    placeholder={'{\n  "headers": {\n    "X-Docs-Env": "staging"\n  },\n  "schema_mapping": {\n    "title": "h1"\n  }\n}'}
                    rows={10}
                    value={form.advancedJson}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, advancedJson: event.target.value }))
                    }
                  />
                </label>
              </article>

              <div className="formFooter">
                <button type="button" className="secondaryButton" disabled={loadingSource || submitting}>
                  Test Connection
                </button>
                <button type="submit" className="primaryButton" disabled={loadingSource || submitting}>
                  <Icon name="rocket_launch" />
                  <span>
                    {submitting
                      ? isEditing
                        ? "Saving..."
                        : "Initializing..."
                      : isEditing
                        ? "Save Changes"
                        : "Initialize Source"}
                  </span>
                </button>
              </div>
              {loadingSource ? <div className="inlineNotice">Loading source configuration...</div> : null}
              {message ? <div className="inlineNotice successNotice">{message}</div> : null}
              {error ? <div className="inlineNotice errorNotice">{error}</div> : null}
            </form>
          </article>
        </div>

        <aside className="sideColumn">
          <article className="readinessCard">
            <div className="readinessHero">
              <span className="heroBadge">Pre-check System</span>
            </div>
            <div className="readinessBody">
              <h4>Environment Readiness</h4>
              <ul className="readinessList">
                {readinessChecks.map(([icon, tone, title, text]) => (
                  <li key={title}>
                    <Icon name={icon} className={tone} />
                    <div>
                      <strong>{title}</strong>
                      <span>{text}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </article>

          <article className="miniLogCard addMiniLogCard">
            <div className="miniLogHeader">
              <span>System Logs</span>
              <div className="miniStatus">
                <span className="liveDot" />
                <span>STREAMING</span>
              </div>
            </div>
            <div className="miniLogBody">
              {pipelineLogs.slice(0, 4).map(([time, , message]) => (
                <p key={`${time}-${message}`}>
                  <span>[{time}]</span> {message}
                </p>
              ))}
            </div>
          </article>

          <article className="noteCard">
            <Icon name="lightbulb" className="warmIcon" />
            <h4>Technical Note</h4>
            <p>
              Ensure your endpoint supports <code>Cross-Origin Resource Sharing (CORS)</code> if you intend to browse documentation directly through the DocsMCP web interface.
            </p>
          </article>
        </aside>
      </section>

      <footer className="mobileActionFooter">
        <button type="button" className="mobileFooterClose">
          <Icon name="close" />
        </button>
        <button type="button" className="mobileFooterSave">
          Save Source
        </button>
      </footer>
    </>
  );
}

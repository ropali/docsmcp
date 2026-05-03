import { useMemo, useState } from "react";
import { createSource } from "../api";
import Icon from "../components/Icon";
import { readinessChecks, pipelineLogs } from "../data/mockData";

const protocolOptions = [
  { label: "HTTPS / REST API", value: "URL" },
  { label: "GraphQL", value: "URL" },
  { label: "Local Filesystem", value: "UNSUPPORTED" },
  { label: "Git Repository", value: "UNSUPPORTED" },
];

export default function AddSourceScreen({ onSourceCreated }) {
  const [form, setForm] = useState({
    name: "",
    source_type: "URL",
    base_url: "",
    protocol: "HTTPS / REST API",
  });
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const selectedProtocol = useMemo(
    () => protocolOptions.find((option) => option.label === form.protocol) || protocolOptions[0],
    [form.protocol],
  );

  return (
    <>
      <section className="pageHeader narrow addSourceHeader">
        <div>
          <div className="breadcrumbs">
            <span>Sources</span>
            <Icon name="chevron_right" className="tinyIcon" />
            <span className="current">New Connection</span>
          </div>
          <h2 className="pageTitle">Add New Source</h2>
          <p className="pageDescription">
            Connect a new external knowledge base, API endpoint, or local documentation directory to the DocsMCP index for real-time semantic search and context injection.
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

                if (selectedProtocol.value === "UNSUPPORTED") {
                  setError("This protocol is not supported by the current backend APIs.");
                  return;
                }

                setSubmitting(true);
                try {
                  const response = await createSource({
                    name: form.name,
                    source_type: selectedProtocol.value,
                    base_url: form.base_url,
                  });
                  setMessage(response.message || "Source created.");
                  if (response?.data?.id) {
                    onSourceCreated(response.data.id, response.data.name);
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
                <div className="field">
                  <span>Sync Frequency</span>
                  <div className="segmentedRow">
                    <button type="button" className="segmentButton">REALTIME</button>
                    <button type="button" className="segmentButton active">HOURLY</button>
                    <button type="button" className="segmentButton">DAILY</button>
                  </div>
                </div>

                <div className="field">
                  <span>Authentication</span>
                  <div className="authCard">
                    <Icon name="key" className="fieldIcon" />
                    <span>Bearer Token Required</span>
                    <button type="button" className="textAction">Configure</button>
                  </div>
                </div>
              </div>

              <div className="formFooter">
                <button type="button" className="secondaryButton">Test Connection</button>
                <button type="submit" className="primaryButton" disabled={submitting}>
                  <Icon name="rocket_launch" />
                  <span>{submitting ? "Initializing..." : "Initialize Source"}</span>
                </button>
              </div>
              {message ? <div className="inlineNotice successNotice">{message}</div> : null}
              {error ? <div className="inlineNotice errorNotice">{error}</div> : null}
            </form>
          </article>

          <article className="collapseCard advancedSettingsCard">
            <div className="collapseHead">
              <div className="inlineGroup">
                <Icon name="settings_input_component" />
                <span>Advanced Extraction &amp; Schema Mapping</span>
              </div>
              <Icon name="expand_more" />
            </div>
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

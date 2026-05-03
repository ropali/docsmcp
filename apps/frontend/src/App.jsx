import { useEffect, useState } from "react";
import { listSources } from "./api";
import AppShell from "./components/AppShell";
import AddSourceScreen from "./screens/AddSourceScreen";
import SourceDetailScreen from "./screens/SourceDetailScreen";
import SourcesDashboard from "./screens/SourcesDashboard";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export default function App() {
  const [health, setHealth] = useState("checking");
  const [screen, setScreen] = useState("dashboard");
  const [selectedSourceId, setSelectedSourceId] = useState(null);
  const [selectedSourceName, setSelectedSourceName] = useState("");
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function checkBackend() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/sources`, {
          headers: { Accept: "application/json" },
        });
        if (!cancelled) {
          setHealth(response.ok ? "reachable" : "unavailable");
        }
      } catch {
        if (!cancelled) {
          setHealth("offline");
        }
      }
    }

    checkBackend();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadInitialSource() {
      try {
        const sources = await listSources();
        if (!cancelled && sources.length > 0 && !selectedSourceId) {
          setSelectedSourceId(sources[0].id);
          setSelectedSourceName(sources[0].name);
        }
      } catch {
        // Screen-level data loaders handle user-visible errors.
      }
    }

    loadInitialSource();

    return () => {
      cancelled = true;
    };
  }, [selectedSourceId, reloadToken]);

  let content = (
    <SourcesDashboard
      onNavigate={setScreen}
      onSelectSource={(sourceId, sourceName) => {
        setSelectedSourceId(sourceId);
        setSelectedSourceName(sourceName);
        setScreen("source-detail");
      }}
      reloadToken={reloadToken}
    />
  );

  if (screen === "add-source") {
    content = (
      <AddSourceScreen
        onSourceCreated={(sourceId, sourceName) => {
          setSelectedSourceId(sourceId);
          setSelectedSourceName(sourceName);
          setReloadToken((current) => current + 1);
          setScreen("source-detail");
        }}
      />
    );
  }

  if (screen === "source-detail") {
    content = (
      <SourceDetailScreen
        sourceId={selectedSourceId}
        reloadToken={reloadToken}
        onRefresh={() => setReloadToken((current) => current + 1)}
        onSourceLoaded={(source) => {
          setSelectedSourceName(source.name);
        }}
      />
    );
  }

  return (
    <AppShell
      currentScreen={screen}
      onNavigate={setScreen}
      health={health}
      detailTitle={selectedSourceName}
      fullBleedTopbar={screen === "source-detail"}
    >
      {content}
    </AppShell>
  );
}

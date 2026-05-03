import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function AppShell({
  currentScreen,
  onNavigate,
  health,
  detailTitle,
  children,
  fullBleedTopbar = false,
}) {
  return (
    <div className="appShell">
      <Sidebar currentScreen={currentScreen} onNavigate={onNavigate} />
      <div className="appContent">
        <Topbar
          currentScreen={currentScreen}
          onNavigate={onNavigate}
          health={health}
          detailTitle={detailTitle}
        />
        <main className={`pageCanvas ${fullBleedTopbar ? "fullBleedTopbar" : ""}`}>{children}</main>
      </div>
    </div>
  );
}

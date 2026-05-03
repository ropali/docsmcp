import Icon from "./Icon";
import { navItems, supportItems } from "../data/mockData";

export default function Sidebar({ currentScreen, onNavigate }) {
  const currentNav = ["dashboard", "add-source", "edit-source", "source-detail"].includes(currentScreen)
    ? "sources"
    : currentScreen;
  const isDashboard = currentScreen === "dashboard";

  return (
    <aside className={`sidebar ${isDashboard ? "dashboardSidebar" : ""}`}>
      <div className="sidebarBrand">
        <div className="sidebarBrandMark">
          <Icon name="database" fill />
        </div>
        <div>
          <h1>DocsMCP</h1>
          <p>v1.0.4 • Stable</p>
        </div>
      </div>

      <nav className="sidebarNav">
        {navItems.map((item) => {
          const isActive = item.id === currentNav;
          const targetByItem = {
            dashboard: "dashboard",
            sources: "dashboard",
            logs: currentScreen,
            settings: currentScreen,
          };
          return (
            <button
              key={item.id}
              type="button"
              className={`navItem ${isActive ? "active" : ""}`}
              onClick={() => onNavigate(targetByItem[item.id])}
            >
              <Icon name={item.icon} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebarFooter">
        {supportItems.map((item) => (
          <button key={item.id} type="button" className="navItem subdued">
            <Icon name={item.icon} />
            <span>{item.label}</span>
          </button>
        ))}

        <div className="engineStatus">
          <div className="engineLabel">System Engine</div>
          <div className="engineValue">
            <span className="liveDot" />
            <span>v1.0.4 - Online</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

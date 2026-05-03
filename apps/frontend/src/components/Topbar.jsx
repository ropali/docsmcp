import Icon from "./Icon";

export default function Topbar({ currentScreen, onNavigate, health, detailTitle }) {
  const isDashboard = currentScreen === "dashboard";
  const isDetail = currentScreen === "source-detail";
  const isAdd = currentScreen === "add-source";

  return (
    <header className={`topbar ${isDetail ? "detailTopbar" : ""} ${isDashboard ? "dashboardTopbar" : ""}`}>
      <div className="topbarLeft">
        {isDetail ? (
          <div className="crumbs">
            <span>Sources /</span>
            <strong>{detailTitle || "Source Detail"}</strong>
          </div>
        ) : isDashboard ? (
          <div className="dashboardTopbarLeft">
            <span className="dashboardWordmark">DocsMCP</span>
            <div className="searchWrap dashboardSearch">
              <Icon name="search" className="searchIcon" />
              <input className="searchInput dashboardSearchInput" placeholder="Search sources..." type="text" />
            </div>
          </div>
        ) : (
          <div className="searchWrap">
            <Icon name="search" className="searchIcon" />
            <input
              className="searchInput"
              placeholder={isAdd ? "Search documentation sources..." : "Search sources..."}
              type="text"
            />
          </div>
        )}
      </div>

      <div className="topbarRight">
        <div className={`topbarControls ${isDetail || isAdd ? "detailControls" : ""}`}>
          <button type="button" className="iconButton">
            <Icon name="notifications" />
          </button>
          <button type="button" className="iconButton">
            <Icon name="settings" />
          </button>
          <button type="button" className="iconButton">
            <Icon name="help" />
          </button>
        </div>

        {isDetail ? (
          <div className="detailProfile">
            <div className="avatarPhoto" title={`Backend ${health}`}>
              <img
                alt="User profile"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuCH_wAwZVMqlziwwHAN9F7Hm77YSa5UdjWzZrZALH-YB-MtEC83rxj8qHMmLfI_E64GQshCrA0vS_4NnEmBZ7djJoKpO574Pwvp8ucjotQGniOU0OHzEz6hUFq8ZT-fOzdp6SlPxkC0LEJ8jWcPSeBbRkYHy1ySyNxgQ7WaDqNJnCh4gEnzLtl4HLz-QZLzeNLYz6T2yXB4yRulp5Y8X355IGBTlsz6nbk6S6OCzPRgg-_n64TfNv6j5Sbs6iXPOqmrh4h8733bHsY"
              />
            </div>
          </div>
        ) : isAdd ? (
          <div className="userBlock addUserBlock">
            <div className="userMeta addUserMeta">
              <strong>DevAdmin</strong>
              <span>Administrator</span>
            </div>
            <div className="avatarPhoto">
              <img
                alt="User profile"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuAGMgfFfmmOxOdjlH4TKIja1ZL4EZCgvZ9GfQNTDVwGdMd02nrKWGm8yZIMrFiaKJjc29WeSoHIkIq0w8CPz1K7QGk1lNalEk0jSqdPAPIaExcdZ1rQ9KCxcOrL4St6DSKhC3IV6-at755ZyWO1gSGghlt7RxeqHz-jvXxzfgyuukGtLoi0Tv6iydwvvd28myhJ2WkNyYi59uW6X39KJob64Nj5NoXRTeqwlUNpXPWAjZ1tLqCUBPTy0eo-5rjs_cNrKK3vX9Cwp9I"
              />
            </div>
          </div>
        ) : (
          <div className="userBlock">
            <div className="userMeta">
              <strong>DevAdmin</strong>
              <span>Administrator</span>
            </div>
            <button type="button" className={`avatar ${isDashboard ? "innerGlow" : ""}`} onClick={() => onNavigate("source-detail")}>
              {isDashboard ? "JD" : "DA"}
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

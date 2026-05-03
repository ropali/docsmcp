export default function LogPanel({ title, status, rows, compact = false }) {
  return (
    <section className={`logPanel ${compact ? "compact" : ""}`}>
      <div className="logPanelHeader">
        <div className="logPanelTitle">
          <span className="liveDot" />
          <strong>{title}</strong>
        </div>
        <span className="logPanelStatus">{status}</span>
      </div>
      <div className="logPanelBody">
        {rows.map(([time, level, message], index) => (
          <div key={`${time}-${index}`} className="logRow">
            <span className="logTime">[{time}]</span>
            {level ? <span className={`logLevel ${level.toLowerCase()}`}>{level}</span> : null}
            <span className={`logMessage ${message === "_" ? "cursor" : ""}`}>{message}</span>
          </div>
        ))}
      </div>
      {!compact ? (
        <div className="logPanelFooter">
          <button type="button" className="ghostTextButton">
            Clear Terminal
          </button>
        </div>
      ) : null}
    </section>
  );
}

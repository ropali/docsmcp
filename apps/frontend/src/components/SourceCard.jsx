import Icon from "./Icon";

export default function SourceCard({ source, onOpenDetail, onRefresh, onEdit }) {
  const syncing = Boolean(source.progress);

  return (
    <article
      className={`sourceCard ${syncing ? "syncing" : ""}`}
      onClick={onOpenDetail}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          onOpenDetail();
        }
      }}
      role="button"
      tabIndex={0}
    >
      {syncing ? <div className="sourceProgress" style={{ width: `${source.progress}%` }} /> : null}

      <div className="sourceCardMain">
        <div className={`sourceGlyph tone-${source.iconTone}`}>
          <Icon name={source.icon} className={syncing ? "pulse" : ""} />
        </div>

        <div className="sourceContent">
          <h3>{source.name}</h3>
          <div className="sourceEndpoint">{source.endpoint}</div>
          <div className="sourceBadges">
            <span className={`badge type ${syncing ? "neutral" : source.iconTone}`}>{source.type}</span>
            <span className="badge subtle">{source.meta}</span>
          </div>
        </div>
      </div>

      <div className="sourceActions">
        <div className={`sourceStatus ${source.statusTone}`}>{source.status}</div>
        <div className="sourceActionButtons">
          <button
            type="button"
            className="iconButton subtleIcon"
            onClick={(event) => {
              event.stopPropagation();
              onEdit?.();
            }}
          >
            <Icon name="edit" />
          </button>
          {onRefresh ? (
            <button
              type="button"
              className="iconButton subtleIcon"
              onClick={(event) => {
                event.stopPropagation();
                onRefresh();
              }}
            >
              <Icon name={syncing ? "stop" : "refresh"} />
            </button>
          ) : null}
          {onRefresh ? (
            <button
              type="button"
              className="iconButton darkIcon"
              onClick={(event) => {
                event.stopPropagation();
                onRefresh();
              }}
            >
              <Icon name={syncing ? "stop" : "play_arrow"} />
            </button>
          ) : null}
        </div>
      </div>
    </article>
  );
}

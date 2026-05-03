import Icon from "./Icon";

export default function StatCard({ label, value, meta, icon, tone = "default" }) {
  return (
    <article className={`statCard tone-${tone}`}>
      <div className="statHeader">
        <span className="statLabel">{label}</span>
        <Icon name={icon} className="statIcon" />
      </div>
      <div className="statBody">
        <div className="statValue">{value}</div>
        <div className="statMeta">{meta}</div>
      </div>
    </article>
  );
}

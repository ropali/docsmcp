export default function Icon({ name, className = "", fill = false }) {
  return (
    <span
      className={`material-symbols-outlined ${className}`.trim()}
      style={{
        fontVariationSettings: `'FILL' ${fill ? 1 : 0}, 'wght' 400, 'GRAD' 0, 'opsz' 24`,
      }}
      aria-hidden="true"
    >
      {name}
    </span>
  );
}

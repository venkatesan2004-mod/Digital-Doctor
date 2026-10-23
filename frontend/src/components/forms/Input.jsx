import React from 'react';

export function Input({
  label,
  hint,
  error,
  isTouch = false,
  className = '',
  id,
  ...props
}) {
  const inputId = id || props.name || Math.random().toString();
  const touchClass = isTouch ? 'input-touch' : '';

  return (
    <div className="form-group">
      {label && <label htmlFor={inputId} className="form-label">{label}</label>}
      <input
        id={inputId}
        className={`input-text ${touchClass} ${className}`.trim()}
        {...props}
      />
      {hint && !error && <span className="form-hint">{hint}</span>}
      {error && <span className="form-hint" style={{ color: 'var(--color-danger)' }}>{error}</span>}
    </div>
  );
}

export function Select({
  label,
  hint,
  error,
  options = [],
  className = '',
  id,
  ...props
}) {
  const selectId = id || props.name || Math.random().toString();

  return (
    <div className="form-group">
      {label && <label htmlFor={selectId} className="form-label">{label}</label>}
      <select
        id={selectId}
        className={`select-box ${className}`.trim()}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {hint && !error && <span className="form-hint">{hint}</span>}
      {error && <span className="form-hint" style={{ color: 'var(--color-danger)' }}>{error}</span>}
    </div>
  );
}

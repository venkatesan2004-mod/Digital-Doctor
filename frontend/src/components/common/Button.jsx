import React from 'react';

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  isTouch = false,
  isLoading = false,
  disabled = false,
  className = '',
  ...props
}) {
  const variantClass = `btn-${variant}`;
  const touchClass = isTouch ? 'btn-touch-large' : '';
  const combinedClasses = `btn ${variantClass} ${touchClass} ${className}`.trim();

  return (
    <button
      className={combinedClasses}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }} />
      ) : null}
      {children}
    </button>
  );
}

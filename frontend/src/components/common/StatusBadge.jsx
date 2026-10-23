import React from 'react';
import { useI18n } from '../../i18n';

export function StatusBadge({ status, label }) {
  let badgeType = 'badge-info';
  const s = String(status).toUpperCase();

  if (s.includes('APPROVED') || s === 'ACTIVE' || s === 'COMPLETED' || s === 'PROCESSED') {
    badgeType = 'badge-success';
  } else if (s.includes('PENDING') || s.includes('REVIEW') || s === 'CREATED') {
    badgeType = 'badge-warning';
  } else if (s.includes('REJECTED') || s === 'CANCELLED' || s === 'EXPIRED' || s === 'EMERGENCY_ESCALATION') {
    badgeType = 'badge-danger';
  }

  return (
    <span className={`badge ${badgeType}`}>
      {label || status}
    </span>
  );
}

export function LoadingState({ message = 'Loading...' }) {
  return (
    <div className="state-container">
      <div className="spinner" />
      <p style={{ color: 'var(--color-text-muted)' }}>{message}</p>
    </div>
  );
}

export function EmptyState({ title = 'No records found', message, action }) {
  return (
    <div className="state-container">
      <div style={{ fontSize: '40px', color: 'var(--color-text-muted)' }}>📋</div>
      <h3>{title}</h3>
      {message && <p>{message}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ title = 'Something went wrong', message, onRetry }) {
  return (
    <div className="state-container">
      <div style={{ fontSize: '40px', color: 'var(--color-danger)' }}>⚠️</div>
      <h3 style={{ color: 'var(--color-danger)' }}>{title}</h3>
      {message && <p>{message}</p>}
      {onRetry && (
        <button className="btn btn-secondary" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function LanguageSwitcher({ isKiosk = false }) {
  const { lang, setLang } = useI18n();

  return (
    <div style={{ display: 'inline-flex', gap: '4px', background: 'var(--color-bg-muted)', padding: '4px', borderRadius: 'var(--border-radius-sm)' }}>
      <button
        type="button"
        className={`btn ${lang === 'en' ? 'btn-primary' : 'btn-secondary'}`}
        style={{
          minHeight: isKiosk ? '44px' : '36px',
          padding: isKiosk ? '6px 16px' : '4px 10px',
          fontSize: isKiosk ? 'var(--font-size-base)' : 'var(--font-size-sm)',
        }}
        onClick={() => setLang('en')}
      >
        English
      </button>
      <button
        type="button"
        className={`btn ${lang === 'ta' ? 'btn-primary' : 'btn-secondary'}`}
        style={{
          minHeight: isKiosk ? '44px' : '36px',
          padding: isKiosk ? '6px 16px' : '4px 10px',
          fontSize: isKiosk ? 'var(--font-size-base)' : 'var(--font-size-sm)',
        }}
        onClick={() => setLang('ta')}
      >
        தமிழ் (Tamil)
      </button>
    </div>
  );
}

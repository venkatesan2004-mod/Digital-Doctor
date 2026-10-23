import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '../../i18n';
import { LanguageSwitcher } from '../../components/common/StatusBadge';

export function KioskWelcome() {
  const { t } = useI18n();
  const navigate = useNavigate();

  return (
    <div className="kiosk-shell">
      <header className="kiosk-header">
        <div className="kiosk-branding">
          <div className="kiosk-logo-badge">⚕️</div>
          <div>
            <h1 className="kiosk-title">{t('app.title')}</h1>
            <p className="kiosk-subtitle">{t('app.hospitalName')}</p>
          </div>
        </div>
        <div className="kiosk-header-actions">
          <LanguageSwitcher isKiosk={true} />
        </div>
      </header>

      <main className="kiosk-main">
        {/* Emergency Triage Red-Flag Warning Banner */}
        <div className="emergency-banner" role="alert">
          <div style={{ fontSize: '36px' }}>🚨</div>
          <div>
            <h4>{t('kiosk.emergencyTitle')}</h4>
            <p style={{ margin: 0, fontWeight: 500 }}>{t('kiosk.emergencyNotice')}</p>
          </div>
        </div>

        <div className="kiosk-welcome-card">
          <div className="kiosk-welcome-hero">
            <h2 className="kiosk-welcome-title">{t('app.welcome')}</h2>
            <p style={{ fontSize: 'var(--font-size-lg)', maxWidth: '600px', margin: '0 auto' }}>
              {t('app.tagline')}
            </p>
          </div>

          <div className="kiosk-action-grid">
            <button
              className="kiosk-big-btn"
              onClick={() => navigate('/kiosk/verify?mode=start')}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 4v16m8-8H4" />
              </svg>
              <span className="btn-label">{t('kiosk.startConsultation')}</span>
              <span className="btn-sub">{t('kiosk.startSubtitle')}</span>
            </button>

            <button
              className="kiosk-big-btn"
              onClick={() => navigate('/kiosk/verify?mode=resume')}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span className="btn-label">{t('kiosk.resumeConsultation')}</span>
              <span className="btn-sub">{t('kiosk.resumeSubtitle')}</span>
            </button>
          </div>

          <div style={{ textAlign: 'left', background: 'var(--color-bg-base)', padding: 'var(--spacing-5)', borderRadius: 'var(--border-radius-md)' }}>
            <h4 style={{ fontSize: 'var(--font-size-base)', marginBottom: 'var(--spacing-1)' }}>ℹ️ Instructions</h4>
            <p style={{ fontSize: 'var(--font-size-sm)', margin: '0 0 var(--spacing-2)' }}>
              {t('kiosk.instructions')}
            </p>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
              {t('kiosk.privacyNotice')}
            </p>
          </div>
        </div>
      </main>

      <footer className="kiosk-footer">
        <span>© 2026 {t('app.hospitalName')} &bull; Digital Doctor Consultation System</span>
        <span>Version 1.0 (Demo Mode)</span>
      </footer>
    </div>
  );
}

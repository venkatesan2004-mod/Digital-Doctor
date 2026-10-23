import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '../../i18n';
import { LanguageSwitcher } from '../../components/common/StatusBadge';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/forms/Input';
import { api } from '../../api/client';
import { useToast } from '../../components/notifications/ToastProvider';

export function KioskVerify() {
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [step, setStep] = useState('lookup'); // 'lookup' | 'verify' | 'select_session'
  const [regNumber, setRegNumber] = useState('');
  const [lookupData, setLookupData] = useState(null);
  const [secFactor, setSecFactor] = useState('');
  const [authData, setAuthData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // 1. Look up registration
  const handleLookup = async (e) => {
    e.preventDefault();
    if (!regNumber.trim()) return;
    setIsLoading(true);
    try {
      const data = await api.kioskLookup(regNumber.trim());
      setLookupData(data);
      setStep('verify');
    } catch (err) {
      addToast(err.message || 'Registration lookup failed', 'danger');
    } finally {
      setIsLoading(false);
    }
  };

  // 2. Verify secondary factor
  const handleVerify = async (e) => {
    e.preventDefault();
    if (!secFactor.trim()) return;
    setIsLoading(true);
    try {
      const data = await api.kioskVerify(regNumber.trim(), secFactor.trim());
      setAuthData(data);
      // Store temporary kiosk session token
      sessionStorage.setItem('dd_kiosk_token', data.session_token);
      sessionStorage.setItem('dd_kiosk_patient', JSON.stringify({
        patient_id: data.patient_id,
        patient_name: data.patient_full_name,
        mrn: data.patient_mrn,
        doctor_name: data.doctor_name,
        reg_number: data.registration_number,
      }));

      // If resumable sessions exist, allow patient to choose; otherwise start fresh
      if (data.resumable_sessions && data.resumable_sessions.length > 0) {
        setStep('select_session');
      } else {
        await startOrResumeSession(null);
      }
    } catch (err) {
      addToast(err.message || 'Verification failed', 'danger');
    } finally {
      setIsLoading(false);
    }
  };

  // 3. Start or Resume session
  const startOrResumeSession = async (existingSessionId = null) => {
    setIsLoading(true);
    try {
      const session = await api.createOrResumeSession(
        regNumber.trim(),
        existingSessionId,
        lang
      );
      sessionStorage.setItem('dd_active_session_id', session.session_id);
      addToast(session.is_resumed ? 'Session resumed.' : 'New consultation session started.', 'success');
      navigate('/kiosk/consultation');
    } catch (err) {
      addToast(err.message || 'Session initialization failed', 'danger');
    } finally {
      setIsLoading(false);
    }
  };

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
          <Button variant="secondary" onClick={() => navigate('/kiosk')}>
            Back to Welcome
          </Button>
        </div>
      </header>

      <main className="kiosk-main">
        <div className="kiosk-welcome-card" style={{ maxWidth: '640px' }}>
          {step === 'lookup' && (
            <form onSubmit={handleLookup}>
              <h2 style={{ marginBottom: 'var(--spacing-2)' }}>{t('kiosk.enterRegNumber')}</h2>
              <p style={{ marginBottom: 'var(--spacing-6)' }}>{t('kiosk.instructions')}</p>

              <Input
                isTouch={true}
                placeholder={t('kiosk.regNumberPlaceholder')}
                value={regNumber}
                onChange={(e) => setRegNumber(e.target.value.toUpperCase())}
                autoFocus
              />

              <div style={{ marginTop: 'var(--spacing-6)' }}>
                <Button
                  type="submit"
                  variant="primary"
                  isTouch={true}
                  style={{ width: '100%' }}
                  disabled={!regNumber.trim() || isLoading}
                  isLoading={isLoading}
                >
                  {t('kiosk.lookupBtn')} &rarr;
                </Button>
              </div>

              <div style={{ marginTop: 'var(--spacing-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                Demo Registrations: <strong>DD-202610-KART01</strong> (Birth Year 1985) or <strong>DD-202610-MEEN02</strong> (Birth Year 1990)
              </div>
            </form>
          )}

          {step === 'verify' && lookupData && (
            <form onSubmit={handleVerify}>
              <h2 style={{ marginBottom: 'var(--spacing-2)' }}>{t('kiosk.secondaryVerificationTitle')}</h2>
              <div style={{ background: 'var(--color-bg-base)', padding: 'var(--spacing-4)', borderRadius: 'var(--border-radius-sm)', marginBottom: 'var(--spacing-4)', textAlign: 'left' }}>
                <div>{t('kiosk.verifiedAs')} <strong>{lookupData.masked_patient_name}</strong></div>
                <div>{t('kiosk.department')} {lookupData.department_name}</div>
                <div>{t('kiosk.assignedDoctor')} {lookupData.doctor_name}</div>
              </div>

              <p style={{ marginBottom: 'var(--spacing-4)' }}>
                {lookupData.verification_factor_prompt || t('kiosk.secondaryVerificationPrompt')}
              </p>

              <Input
                isTouch={true}
                type="text"
                placeholder="e.g. 1985"
                maxLength={4}
                value={secFactor}
                onChange={(e) => setSecFactor(e.target.value.trim())}
                autoFocus
              />

              <div style={{ marginTop: 'var(--spacing-6)', display: 'flex', gap: 'var(--spacing-3)' }}>
                <Button
                  type="button"
                  variant="secondary"
                  isTouch={true}
                  style={{ flex: 1 }}
                  onClick={() => setStep('lookup')}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  isTouch={true}
                  style={{ flex: 2 }}
                  disabled={!secFactor.trim() || isLoading}
                  isLoading={isLoading}
                >
                  {t('kiosk.verifyBtn')} &rarr;
                </Button>
              </div>
            </form>
          )}

          {step === 'select_session' && authData && (
            <div>
              <h2 style={{ marginBottom: 'var(--spacing-2)' }}>{t('kiosk.activeSessionsFound')}</h2>
              <p style={{ marginBottom: 'var(--spacing-4)' }}>
                Patient: <strong>{authData.patient_full_name}</strong> &bull; Clinician: <strong>{authData.doctor_name}</strong>
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-3)', marginBottom: 'var(--spacing-6)' }}>
                {authData.resumable_sessions.map((sess) => (
                  <div
                    key={sess.session_id}
                    style={{
                      border: '2px solid var(--color-primary-border)',
                      borderRadius: 'var(--border-radius-md)',
                      padding: 'var(--spacing-4)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      textAlign: 'left',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600 }}>Session: {sess.session_id.slice(0, 8)}...</div>
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                        Started: {new Date(sess.started_at).toLocaleTimeString()} &bull; Messages: {sess.message_count}
                      </div>
                    </div>
                    <Button
                      variant="primary"
                      onClick={() => startOrResumeSession(sess.session_id)}
                      isLoading={isLoading}
                    >
                      {t('kiosk.resumeSessionBtn')}
                    </Button>
                  </div>
                ))}
              </div>

              <Button
                variant="secondary"
                isTouch={true}
                style={{ width: '100%' }}
                onClick={() => startOrResumeSession(null)}
                isLoading={isLoading}
              >
                + {t('kiosk.createNewSessionBtn')}
              </Button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

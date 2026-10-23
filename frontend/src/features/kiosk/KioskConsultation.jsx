import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '../../i18n';
import { LanguageSwitcher } from '../../components/common/StatusBadge';
import { Button } from '../../components/common/Button';
import { ChatMessage } from '../../components/clinical/ChatMessage';
import { DocumentUploader } from '../../components/clinical/DocumentUploader';
import { ConfirmDialog } from '../../components/common/Modal';
import { api } from '../../api/client';
import { useToast } from '../../components/notifications/ToastProvider';

export function KioskConsultation() {
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const { addToast } = useToast();

  const sessionId = sessionStorage.getItem('dd_active_session_id');
  const patientData = JSON.parse(sessionStorage.getItem('dd_kiosk_patient') || '{}');

  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [activeTab, setActiveTab] = useState('encounters');
  const [clinicalHistory, setClinicalHistory] = useState(null);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isCloseDialogOpen, setIsCloseDialogOpen] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  const messagesEndRef = useRef(null);

  // If no session token, redirect to kiosk home
  useEffect(() => {
    if (!sessionId || !sessionStorage.getItem('dd_kiosk_token')) {
      navigate('/kiosk');
    }
  }, [sessionId, navigate]);

  // Load message history and patient clinical records
  const loadData = async () => {
    if (!sessionId) return;
    try {
      const [msgs, history] = await Promise.all([
        api.getSessionMessages(sessionId),
        api.getSessionClinicalHistory(sessionId).catch(() => null),
      ]);
      setMessages(msgs || []);
      setClinicalHistory(history);
    } catch (err) {
      addToast(err.message || 'Failed to load consultation records', 'danger');
    }
  };

  useEffect(() => {
    loadData();
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  // Send message
  const handleSendMessage = async (e, customText = null) => {
    if (e) e.preventDefault();
    const query = (customText || inputText).trim();
    if (!query || isSending) return;

    setInputText('');
    setIsSending(true);

    // Optimistic patient bubble
    const tempPatientMsg = {
      id: Date.now(),
      sender_type: 'PATIENT',
      message_text: query,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempPatientMsg]);

    try {
      const aiResponse = await api.sendConsultationMessage(sessionId, query, lang);
      // Reload full conversation history from server
      const updatedMsgs = await api.getSessionMessages(sessionId);
      setMessages(updatedMsgs);
    } catch (err) {
      addToast(err.message || 'Failed to retrieve AI guidance', 'danger');
    } finally {
      setIsSending(false);
    }
  };

  // Close consultation & Purge Kiosk State
  const handleConfirmClose = async () => {
    setIsClosing(true);
    try {
      await api.closeSession(sessionId, 'Patient Completed Consultation');
      addToast('Consultation completed and saved securely. Kiosk reset.', 'success');
    } catch (err) {
      console.warn('Error during close:', err);
    } finally {
      // Invalidate all tokens & purge local/session storage
      sessionStorage.removeItem('dd_kiosk_token');
      sessionStorage.removeItem('dd_kiosk_patient');
      sessionStorage.removeItem('dd_active_session_id');
      setIsClosing(false);
      setIsCloseDialogOpen(false);
      navigate('/kiosk');
    }
  };

  return (
    <div className="kiosk-shell">
      {/* Kiosk Header */}
      <header className="kiosk-header">
        <div className="kiosk-branding">
          <div className="kiosk-logo-badge">⚕️</div>
          <div>
            <h1 className="kiosk-title" style={{ fontSize: 'var(--font-size-lg)' }}>
              {t('app.title')} &bull; {patientData.patient_name || 'Patient Consultation'}
            </h1>
            <p className="kiosk-subtitle">
              MRN: {patientData.mrn || 'N/A'} &bull; Clinician: Dr. {patientData.doctor_name || 'Physician'}
            </p>
          </div>
        </div>

        <div className="kiosk-header-actions">
          <Button variant="secondary" onClick={() => setIsUploadOpen(true)}>
            📎 {t('consultation.uploadDocumentBtn')}
          </Button>
          <LanguageSwitcher isKiosk={true} />
          <Button variant="danger" onClick={() => setIsCloseDialogOpen(true)}>
            🚪 {t('kiosk.closeConsultation')}
          </Button>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="kiosk-main" style={{ padding: 'var(--spacing-4)' }}>
        <div className="consultation-workspace">
          {/* Left Chat Consultation Panel */}
          <div className="chat-panel">
            <div className="chat-messages-container">
              {messages.length === 0 ? (
                <div style={{ textAlign: 'center', margin: 'auto', maxWidth: '480px' }}>
                  <div style={{ fontSize: '48px', marginBottom: 'var(--spacing-3)' }}>🩺</div>
                  <h3>{t('app.welcome')}</h3>
                  <p>{t('consultation.chatPlaceholder')}</p>
                </div>
              ) : (
                messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
              )}

              {isSending && (
                <div className="message-bubble message-ai" style={{ maxWidth: '320px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2px' }} />
                    <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
                      {t('consultation.thinking')}
                    </span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input & Suggestion Pills */}
            <div className="chat-input-area">
              <div className="suggestion-pills-row">
                <button
                  type="button"
                  className="touch-pill"
                  onClick={() => handleSendMessage(null, t('consultation.suggestionFever'))}
                >
                  🌡️ {t('consultation.suggestionFever')}
                </button>
                <button
                  type="button"
                  className="touch-pill"
                  onClick={() => handleSendMessage(null, t('consultation.suggestionCough'))}
                >
                  🗣️ {t('consultation.suggestionCough')}
                </button>
                <button
                  type="button"
                  className="touch-pill"
                  onClick={() => handleSendMessage(null, t('consultation.suggestionBP'))}
                >
                  💊 {t('consultation.suggestionBP')}
                </button>
              </div>

              <form className="chat-form" onSubmit={handleSendMessage}>
                <input
                  type="text"
                  className="input-text"
                  placeholder={t('consultation.chatPlaceholder')}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  disabled={isSending}
                />
                <Button
                  type="submit"
                  variant="primary"
                  disabled={!inputText.trim() || isSending}
                  isLoading={isSending}
                  style={{ minWidth: '100px' }}
                >
                  {t('consultation.send')}
                </Button>
              </form>
            </div>
          </div>

          {/* Right Clinical History Drawer */}
          <div className="clinical-drawer">
            <div className="drawer-tabs">
              <button
                className={`drawer-tab ${activeTab === 'encounters' ? 'active' : ''}`}
                onClick={() => setActiveTab('encounters')}
              >
                {t('consultation.tabEncounters')}
              </button>
              <button
                className={`drawer-tab ${activeTab === 'prescriptions' ? 'active' : ''}`}
                onClick={() => setActiveTab('prescriptions')}
              >
                {t('consultation.tabPrescriptions')}
              </button>
              <button
                className={`drawer-tab ${activeTab === 'labs' ? 'active' : ''}`}
                onClick={() => setActiveTab('labs')}
              >
                {t('consultation.tabLabs')}
              </button>
              <button
                className={`drawer-tab ${activeTab === 'radiology' ? 'active' : ''}`}
                onClick={() => setActiveTab('radiology')}
              >
                {t('consultation.tabRadiology')}
              </button>
            </div>

            <div className="drawer-content">
              {activeTab === 'encounters' && (
                <div>
                  {clinicalHistory?.encounters?.length ? (
                    clinicalHistory.encounters.map((enc) => (
                      <div key={enc.id} className="card" style={{ marginBottom: '8px' }}>
                        <div className="card-body" style={{ padding: '10px' }}>
                          <div style={{ fontSize: '11px', color: 'var(--color-primary)', fontWeight: 600 }}>
                            {enc.date.split('T')[0]} &bull; {enc.source}
                          </div>
                          <div style={{ fontWeight: 600, fontSize: '13px' }}>{enc.chief_complaint}</div>
                          <p style={{ fontSize: '12px', margin: '4px 0 0' }}>{enc.summary}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>No prior encounters recorded.</p>
                  )}
                </div>
              )}

              {activeTab === 'prescriptions' && (
                <div>
                  {clinicalHistory?.prescriptions?.length ? (
                    clinicalHistory.prescriptions.map((rx) => (
                      <div key={rx.id} className="card" style={{ marginBottom: '8px' }}>
                        <div className="card-body" style={{ padding: '10px' }}>
                          <div style={{ fontWeight: 600, fontSize: '13px' }}>{rx.medication_name} ({rx.dosage})</div>
                          <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                            {rx.frequency} &bull; {rx.duration}
                          </div>
                          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                            {rx.instructions} ({rx.date.split('T')[0]})
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>No past prescriptions recorded.</p>
                  )}
                </div>
              )}

              {activeTab === 'labs' && (
                <div>
                  {clinicalHistory?.laboratory_results?.length ? (
                    clinicalHistory.laboratory_results.map((lab) => (
                      <div key={lab.id} className="card" style={{ marginBottom: '8px' }}>
                        <div className="card-body" style={{ padding: '10px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <strong style={{ fontSize: '13px' }}>{lab.test_name}</strong>
                            <span style={{ fontSize: '12px', color: lab.is_abnormal ? 'var(--color-danger)' : 'var(--color-success)', fontWeight: 600 }}>
                              {lab.result_value}
                            </span>
                          </div>
                          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                            Ref: {lab.reference_range} &bull; {lab.date.split('T')[0]}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>No laboratory results on file.</p>
                  )}
                </div>
              )}

              {activeTab === 'radiology' && (
                <div>
                  {clinicalHistory?.radiology_reports?.length ? (
                    clinicalHistory.radiology_reports.map((rad) => (
                      <div key={rad.id} className="card" style={{ marginBottom: '8px' }}>
                        <div className="card-body" style={{ padding: '10px' }}>
                          <div style={{ fontWeight: 600, fontSize: '13px' }}>{rad.procedure_name} ({rad.modality})</div>
                          <div style={{ fontSize: '12px', marginTop: '2px' }}>{rad.impression}</div>
                          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                            {rad.radiologist} &bull; {rad.date.split('T')[0]}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>No radiology reports on file.</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Document Uploader Modal */}
      <DocumentUploader
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        sessionId={sessionId}
        onUploadSuccess={() => loadData()}
      />

      {/* Confirm Session Close Dialog */}
      <ConfirmDialog
        isOpen={isCloseDialogOpen}
        onClose={() => setIsCloseDialogOpen(false)}
        onConfirm={handleConfirmClose}
        title={t('kiosk.closeConfirmTitle')}
        message={t('kiosk.closeConfirmMessage')}
        confirmLabel="Exit Consultation"
        isDanger={true}
        isLoading={isClosing}
      />
    </div>
  );
}

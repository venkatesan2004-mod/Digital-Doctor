import React from 'react';
import { StatusBadge } from '../common/StatusBadge';
import { useI18n } from '../../i18n';

export function ChatMessage({ message }) {
  const { t } = useI18n();
  const isPatient = message.sender_type === 'PATIENT';
  const payload = message.structured_payload;

  if (isPatient) {
    return (
      <div className="message-bubble message-patient">
        <p>{message.message_text}</p>
        <span style={{ fontSize: '10px', opacity: 0.8, display: 'block', textAlign: 'right', marginTop: '4px' }}>
          {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    );
  }

  // AI Assistant Response Card
  const isEmergency = payload?.response_status === 'EMERGENCY_ESCALATION';

  return (
    <div className="message-bubble message-ai">
      <div className="ai-header-badge">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: 700, color: 'var(--color-primary)' }}>🤖 Digital Doctor AI</span>
          <StatusBadge status={isEmergency ? 'EMERGENCY_ESCALATION' : 'DECISION_SUPPORT'} label={isEmergency ? 'EMERGENCY ALERT' : 'Clinical Decision Support'} />
        </div>
        <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
          {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      {/* Emergency Red-Flag Warning Banner */}
      {isEmergency && payload?.safety_alerts?.length > 0 && (
        <div className="emergency-banner" style={{ margin: 'var(--spacing-3) 0' }}>
          <span style={{ fontSize: '24px' }}>🚨</span>
          <div>
            <h4>{t('consultation.safetyAlertTitle')}</h4>
            {payload.safety_alerts.map((alert, idx) => (
              <p key={idx} style={{ fontWeight: 600, color: 'var(--color-danger)', margin: 0 }}>
                {alert}
              </p>
            ))}
          </div>
        </div>
      )}

      {/* Primary Clinical Guidance Answer */}
      <div style={{ fontSize: 'var(--font-size-base)', lineHeight: 1.6, marginBottom: 'var(--spacing-3)' }}>
        <p>{payload?.answer || message.message_text}</p>
      </div>

      {/* Structured Payload Breakdown */}
      {payload && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-3)', borderTop: '1px solid var(--color-bg-subtle)', paddingTop: 'var(--spacing-3)' }}>
          {/* Symptom Summary */}
          {payload.symptom_summary && (
            <div>
              <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                {t('consultation.symptomSummary')}:
              </span>
              <p style={{ fontSize: 'var(--font-size-sm)', margin: '2px 0 0' }}>{payload.symptom_summary}</p>
            </div>
          )}

          {/* Draft Clinical Orders (Awaiting Doctor Review) */}
          {payload.draft_orders && payload.draft_orders.length > 0 && (
            <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 'var(--border-radius-sm)', padding: 'var(--spacing-3)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--spacing-2)' }}>
                <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 700, color: 'var(--color-warning)', textTransform: 'uppercase' }}>
                  ⏳ {t('consultation.draftOrdersTitle')}
                </span>
                <StatusBadge status="PENDING_REVIEW" label={t('consultation.requiresDoctorReviewBadge')} />
              </div>
              <ul style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {payload.draft_orders.map((draft, idx) => (
                  <li key={idx} style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-main)', background: '#ffffff', padding: '6px 10px', borderRadius: '4px', border: '1px solid #fef3c7' }}>
                    <strong>[{draft.order_type}]</strong> {draft.item_name} &mdash; <em>{draft.details}</em>
                    <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                      Rationale: {draft.clinical_rationale}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Clinical Uncertainties & Limitations */}
          {payload.uncertainties && payload.uncertainties.length > 0 && (
            <div>
              <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                ⚠️ {t('consultation.uncertainties')}:
              </span>
              <ul style={{ listStyleType: 'disc', paddingLeft: '20px', fontSize: 'var(--font-size-sm)', margin: '4px 0 0' }}>
                {payload.uncertainties.map((unc, idx) => (
                  <li key={idx}>{unc}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Source Grounding References */}
          {payload.source_references && payload.source_references.length > 0 && (
            <div style={{ background: 'var(--color-bg-muted)', padding: 'var(--spacing-3)', borderRadius: 'var(--border-radius-sm)' }}>
              <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                📚 {t('consultation.sourceReferences')} ({payload.source_references.length}):
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
                {payload.source_references.map((ref, idx) => (
                  <div key={idx} style={{ fontSize: 'var(--font-size-xs)', background: '#ffffff', padding: '6px 10px', borderRadius: '4px', border: '1px solid var(--color-bg-subtle)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600 }}>
                      <span>{ref.title} ({ref.record_type})</span>
                      <span style={{ color: 'var(--color-text-muted)' }}>{ref.date}</span>
                    </div>
                    <div style={{ color: 'var(--color-text-secondary)', marginTop: '2px' }}>{ref.summary}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

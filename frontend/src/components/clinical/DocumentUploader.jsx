import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { api } from '../../api/client';
import { useToast } from '../notifications/ToastProvider';
import { useI18n } from '../../i18n';

export function DocumentUploader({ isOpen, onClose, sessionId, onUploadSuccess }) {
  const { t } = useI18n();
  const { addToast } = useToast();
  const [selectedFile, setSelectedFile] = useState(null);
  const [docType, setDocType] = useState('Medical Report');
  const [isUploading, setIsUploading] = useState(false);
  const [extractedData, setExtractedData] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    try {
      const res = await api.uploadMedicalDocument(sessionId, selectedFile, docType);
      setExtractedData(res);
      addToast('Document analyzed successfully.', 'success');
      if (onUploadSuccess) onUploadSuccess(res);
    } catch (err) {
      addToast(err.message || 'Upload failed', 'danger');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDone = () => {
    setSelectedFile(null);
    setExtractedData(null);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleDone}
      title={t('consultation.uploadModalTitle')}
      footer={
        extractedData ? (
          <Button variant="primary" onClick={handleDone}>
            Done
          </Button>
        ) : (
          <>
            <Button variant="secondary" onClick={handleDone} disabled={isUploading}>
              {t('common.cancel')}
            </Button>
            <Button
              variant="primary"
              onClick={handleUpload}
              disabled={!selectedFile || isUploading}
              isLoading={isUploading}
            >
              Upload & Analyze
            </Button>
          </>
        )
      }
    >
      {!extractedData ? (
        <div>
          <div className="form-group">
            <label className="form-label">Document Category</label>
            <select
              className="select-box"
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
            >
              <option value="Laboratory Report">Laboratory Report</option>
              <option value="Radiology Scan">Radiology / X-Ray Report</option>
              <option value="Previous Prescription">Previous Prescription</option>
              <option value="Discharge Summary">Discharge Summary</option>
            </select>
          </div>

          <div
            style={{
              border: '2px dashed var(--color-primary-border)',
              borderRadius: 'var(--border-radius-md)',
              padding: 'var(--spacing-8)',
              textAlign: 'center',
              backgroundColor: 'var(--color-bg-base)',
              cursor: 'pointer',
            }}
            onClick={() => document.getElementById('file-upload-input').click()}
          >
            <input
              id="file-upload-input"
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
            <div style={{ fontSize: '36px', marginBottom: 'var(--spacing-2)' }}>📄</div>
            <p style={{ fontWeight: 600 }}>{selectedFile ? selectedFile.name : t('consultation.uploadDragDrop')}</p>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              Supported: PDF, PNG, JPG (Max 10MB)
            </span>
          </div>
        </div>
      ) : (
        <div>
          <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', padding: 'var(--spacing-4)', borderRadius: 'var(--border-radius-sm)', marginBottom: 'var(--spacing-4)' }}>
            <h4 style={{ color: 'var(--color-success)', marginBottom: '4px' }}>Extracted Clinical Findings (OCR)</h4>
            <p style={{ fontSize: 'var(--font-size-sm)', margin: 0 }}>{extractedData.ai_summary}</p>
          </div>

          <div className="form-group">
            <label className="form-label">Raw Text Extraction:</label>
            <textarea
              className="textarea-box"
              rows={6}
              readOnly
              value={extractedData.ocr_extracted_text || 'No text extracted'}
            />
          </div>
          <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
            Note: This extraction is decision-support only and has been added to your session for attending doctor review.
          </span>
        </div>
      )}
    </Modal>
  );
}

export function ClinicianApprovalCard({ item, onActionSuccess }) {
  const { t } = useI18n();
  const { addToast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      await api.executeReviewAction(item.item_type, item.item_id, 'APPROVE');
      addToast(t('staff.approvedSuccess'), 'success');
      if (onActionSuccess) onActionSuccess();
    } catch (err) {
      addToast(err.message || 'Approval failed', 'danger');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    try {
      await api.executeReviewAction(item.item_type, item.item_id, 'REJECT', null, rejectReason);
      addToast(t('staff.rejectedSuccess'), 'warning');
      setShowRejectModal(false);
      if (onActionSuccess) onActionSuccess();
    } catch (err) {
      addToast(err.message || 'Rejection failed', 'danger');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="approval-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 700, color: 'var(--color-primary)', textTransform: 'uppercase' }}>
            [{item.item_type.replace('_', ' ')}]
          </span>
          <h3 style={{ fontSize: 'var(--font-size-lg)', marginTop: '2px' }}>{item.item_title}</h3>
          <p style={{ fontSize: 'var(--font-size-sm)', margin: '4px 0', color: 'var(--color-text-secondary)' }}>
            Patient: <strong>{item.patient_name}</strong> (MRN: {item.patient_mrn})
          </p>
          <div style={{ fontSize: 'var(--font-size-sm)', background: '#ffffff', padding: 'var(--spacing-3)', borderRadius: '4px', border: '1px solid #fef3c7', marginTop: 'var(--spacing-2)' }}>
            <strong>Details:</strong> {item.item_details}
            {item.clinical_rationale && (
              <div style={{ marginTop: '4px', color: 'var(--color-text-muted)' }}>
                <strong>AI Rationale:</strong> {item.clinical_rationale}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="approval-card-actions">
        <Button
          variant="danger"
          onClick={() => setShowRejectModal(true)}
          disabled={isSubmitting}
        >
          {t('staff.rejectBtn')}
        </Button>
        <Button
          variant="success"
          onClick={handleApprove}
          isLoading={isSubmitting}
        >
          {t('staff.approveBtn')}
        </Button>
      </div>

      {showRejectModal && (
        <Modal
          isOpen={showRejectModal}
          onClose={() => setShowRejectModal(false)}
          title="Reject Clinical Draft Order"
          footer={
            <>
              <Button variant="secondary" onClick={() => setShowRejectModal(false)}>
                Cancel
              </Button>
              <Button variant="danger" onClick={handleReject} isLoading={isSubmitting}>
                Confirm Rejection
              </Button>
            </>
          }
        >
          <div className="form-group">
            <label className="form-label">{t('staff.rejectionReasonPrompt')}</label>
            <input
              type="text"
              className="input-text"
              placeholder="e.g. Inappropriate dose for renal status / clinically unnecessary"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
            />
          </div>
        </Modal>
      )}
    </div>
  );
}

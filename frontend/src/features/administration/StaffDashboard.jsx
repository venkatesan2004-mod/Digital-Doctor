import React, { useState, useEffect } from 'react';
import { useI18n } from '../../i18n';
import { Button } from '../../components/common/Button';
import { StatusBadge } from '../../components/common/StatusBadge';
import { DataTable } from '../../components/tables/DataTable';
import { ClinicianApprovalCard } from '../../components/clinical/DocumentUploader';
import { LoadingState } from '../../components/common/StatusBadge';
import { api } from '../../api/client';
import { useToast } from '../../components/notifications/ToastProvider';

export function StaffDashboard() {
  const { t } = useI18n();
  const { addToast } = useToast();

  const [activeTab, setActiveTab] = useState('review_queue');
  const [reviewQueue, setReviewQueue] = useState([]);
  const [registrations, setRegistrations] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [healthData, setHealthData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const currentUser = JSON.parse(localStorage.getItem('dd_staff_user') || '{}');

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const [queue, regs, health, logs] = await Promise.all([
        api.getReviewQueue().catch(() => []),
        api.getRegistrations().catch(() => []),
        api.getHealth().catch(() => null),
        api.getAuditLogs(30).catch(() => []),
      ]);
      setReviewQueue(queue || []);
      setRegistrations(regs || []);
      setHealthData(health);
      setAuditLogs(logs || []);
    } catch (err) {
      addToast(err.message || 'Failed to refresh dashboard', 'danger');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const regColumns = [
    { key: 'registration_number', header: 'Reg #' },
    { key: 'patient_name', header: 'Patient Name' },
    { key: 'patient_mrn', header: 'MRN' },
    {
      key: 'consultation_type',
      header: 'Pathway',
      render: (val) => (
        <StatusBadge
          status={val === 'DIRECT_DOCTOR' ? 'INFO' : 'ACTIVE'}
          label={val.replace('_', ' ')}
        />
      ),
    },
    { key: 'department', header: 'Department' },
    { key: 'assigned_doctor', header: 'Assigned Clinician' },
    {
      key: 'registration_time',
      header: 'Registered At',
      render: (val) => new Date(val).toLocaleString(),
    },
  ];

  const auditColumns = [
    { key: 'id', header: 'ID', width: '60px' },
    { key: 'event_type', header: 'Event Type' },
    { key: 'actor_type', header: 'Actor' },
    { key: 'resource_type', header: 'Resource' },
    {
      key: 'created_at',
      header: 'Timestamp',
      render: (val) => new Date(val).toLocaleString(),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-6)' }}>
        <div>
          <h2>{t('staff.dashboardTitle')}</h2>
          <p>
            Welcome, <strong>{currentUser.full_name || 'Clinician'}</strong> &bull; Role: <StatusBadge status="ACTIVE" label={currentUser.role || 'DOCTOR'} />
          </p>
        </div>
        <Button variant="secondary" onClick={loadDashboardData} isLoading={isLoading}>
          🔄 Refresh
        </Button>
      </div>

      {/* Top Metrics Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
            Pending Doctor Approvals
          </div>
          <div className="stat-value" style={{ color: reviewQueue.length > 0 ? 'var(--color-warning)' : 'var(--color-success)' }}>
            {reviewQueue.length}
          </div>
        </div>

        <div className="stat-card">
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
            Total Registrations
          </div>
          <div className="stat-value">{registrations.length}</div>
        </div>

        <div className="stat-card">
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
            AI Engine Provider
          </div>
          <div className="stat-value" style={{ fontSize: 'var(--font-size-2xl)' }}>
            {healthData?.ai_provider?.toUpperCase() || 'MOCK'}
          </div>
        </div>

        <div className="stat-card">
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
            Database System
          </div>
          <div className="stat-value" style={{ fontSize: 'var(--font-size-lg)', color: 'var(--color-success)' }}>
            {healthData?.database || 'Connected'}
          </div>
        </div>
      </div>

      {/* Section Tabs */}
      <div style={{ display: 'flex', gap: 'var(--spacing-2)', borderBottom: '1px solid var(--color-bg-subtle)', marginBottom: 'var(--spacing-6)' }}>
        <button
          className={`btn ${activeTab === 'review_queue' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('review_queue')}
        >
          ⏳ {t('staff.reviewQueue')} ({reviewQueue.length})
        </button>
        <button
          className={`btn ${activeTab === 'registrations' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('registrations')}
        >
          📋 {t('staff.registrations')}
        </button>
        <button
          className={`btn ${activeTab === 'audit_logs' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('audit_logs')}
        >
          🛡️ {t('staff.auditLogs')}
        </button>
        <button
          className={`btn ${activeTab === 'system_health' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('system_health')}
        >
          🩺 {t('staff.systemHealth')}
        </button>
      </div>

      {/* Tab 1: Clinician Review Queue */}
      {activeTab === 'review_queue' && (
        <div>
          <div style={{ marginBottom: 'var(--spacing-4)' }}>
            <h3>Physician Clinical Approval Queue</h3>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
              Mandatory Human-In-The-Loop review. All AI draft recommendations remain un-dispensable until formally signed off.
            </p>
          </div>

          {reviewQueue.length === 0 ? (
            <div className="card" style={{ padding: 'var(--spacing-8)', textAlign: 'center' }}>
              <div style={{ fontSize: '40px', color: 'var(--color-success)', marginBottom: '8px' }}>✓</div>
              <h3>Review Queue Clear</h3>
              <p>No draft prescriptions or orders currently awaiting clinician sign-off.</p>
            </div>
          ) : (
            <div>
              {reviewQueue.map((item) => (
                <ClinicianApprovalCard
                  key={`${item.item_type}_${item.item_id}`}
                  item={item}
                  onActionSuccess={loadDashboardData}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Registrations */}
      {activeTab === 'registrations' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Hospital Registrations (Direct & Digital Doctor)</h3>
          </div>
          <div className="card-body">
            <DataTable
              columns={regColumns}
              data={registrations}
              pageSize={10}
            />
          </div>
        </div>
      )}

      {/* Tab 3: Audit Logs */}
      {activeTab === 'audit_logs' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Immutable Audit Trail Logs</h3>
          </div>
          <div className="card-body">
            <DataTable
              columns={auditColumns}
              data={auditLogs}
              pageSize={10}
            />
          </div>
        </div>
      )}

      {/* Tab 4: System Health */}
      {activeTab === 'system_health' && healthData && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">System Infrastructure & Diagnostics</h3>
          </div>
          <div className="card-body">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-4)' }}>
              <div style={{ padding: 'var(--spacing-4)', background: 'var(--color-bg-base)', borderRadius: 'var(--border-radius-sm)' }}>
                <strong>Application Status:</strong> {healthData.status}
              </div>
              <div style={{ padding: 'var(--spacing-4)', background: 'var(--color-bg-base)', borderRadius: 'var(--border-radius-sm)' }}>
                <strong>Environment:</strong> {healthData.environment}
              </div>
              <div style={{ padding: 'var(--spacing-4)', background: 'var(--color-bg-base)', borderRadius: 'var(--border-radius-sm)' }}>
                <strong>Database Connectivity:</strong> {healthData.database}
              </div>
              <div style={{ padding: 'var(--spacing-4)', background: 'var(--color-bg-base)', borderRadius: 'var(--border-radius-sm)' }}>
                <strong>Vector Store (ChromaDB):</strong> {healthData.vector_store}
              </div>
              <div style={{ padding: 'var(--spacing-4)', background: 'var(--color-bg-base)', borderRadius: 'var(--border-radius-sm)' }}>
                <strong>AI Provider Adapter:</strong> {healthData.ai_provider}
              </div>
              <div style={{ padding: 'var(--spacing-4)', background: 'var(--color-bg-base)', borderRadius: 'var(--border-radius-sm)' }}>
                <strong>Server Timestamp:</strong> {new Date(healthData.timestamp).toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

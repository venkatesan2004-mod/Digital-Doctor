import React, { useState, useEffect } from 'react';
import { useI18n } from '../../i18n';
import { Button } from '../../components/common/Button';
import { Input, Select } from '../../components/forms/Input';
import { StatusBadge } from '../../components/common/StatusBadge';
import { DataTable } from '../../components/tables/DataTable';
import { Modal } from '../../components/common/Modal';
import { api } from '../../api/client';
import { useToast } from '../../components/notifications/ToastProvider';

export function FrontOfficeRegistration() {
  const { t } = useI18n();
  const { addToast } = useToast();

  const [departments, setDepartments] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [registrations, setRegistrations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmationData, setConfirmationData] = useState(null);

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    date_of_birth: '1988-05-12',
    gender: 'Male',
    contact_phone: '+91 98765 00123',
    contact_email: 'patient.synthetic@example.org',
    address: '100, Mount Road, Chennai',
    preferred_language: 'en',
    department_id: '',
    assigned_doctor_id: '',
    consultation_type: 'DIGITAL_DOCTOR',
    secondary_verification_pin: '1988',
  });

  const loadInitialData = async () => {
    setIsLoading(true);
    try {
      const [deps, docs, regs] = await Promise.all([
        api.getDepartments(),
        api.getDoctors(),
        api.getRegistrations(),
      ]);
      setDepartments(deps || []);
      setDoctors(docs || []);
      setRegistrations(regs || []);

      if (deps?.length && !formData.department_id) {
        setFormData((prev) => ({
          ...prev,
          department_id: deps[0].id,
          assigned_doctor_id: docs?.[0]?.id || '',
        }));
      }
    } catch (err) {
      addToast(err.message || 'Failed to load front office data', 'danger');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await api.registerPatient({
        ...formData,
        department_id: parseInt(formData.department_id, 10),
        assigned_doctor_id: parseInt(formData.assigned_doctor_id, 10),
      });
      setConfirmationData(res);
      addToast(res.message, 'success');
      loadInitialData();
    } catch (err) {
      addToast(err.message || 'Registration failed', 'danger');
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns = [
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
    { key: 'assigned_doctor', header: 'Clinician' },
    {
      key: 'registration_time',
      header: 'Time',
      render: (val) => new Date(val).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 'var(--spacing-6)' }}>
        <h2>{t('frontOffice.title')}</h2>
        <p>{t('frontOffice.subtitle')}</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-6)', alignItems: 'start' }}>
        {/* Registration Form */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">New Patient Intake Form</h3>
          </div>
          <div className="card-body">
            <form onSubmit={handleSubmit}>
              {/* Consultation Type Selector */}
              <div className="form-group" style={{ marginBottom: 'var(--spacing-4)' }}>
                <label className="form-label">{t('frontOffice.consultationType')}</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-3)' }}>
                  <button
                    type="button"
                    className={`btn ${formData.consultation_type === 'DIRECT_DOCTOR' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setFormData((p) => ({ ...p, consultation_type: 'DIRECT_DOCTOR' }))}
                  >
                    🏥 Direct Doctor (HIMS)
                  </button>
                  <button
                    type="button"
                    className={`btn ${formData.consultation_type === 'DIGITAL_DOCTOR' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setFormData((p) => ({ ...p, consultation_type: 'DIGITAL_DOCTOR' }))}
                  >
                    🤖 Digital Doctor (Kiosk)
                  </button>
                </div>
                {formData.consultation_type === 'DIRECT_DOCTOR' ? (
                  <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-primary)', marginTop: '4px' }}>
                    Note: Direct Doctor consultations bypass the AI Kiosk and are dispatched directly to the OPD doctor queue.
                  </p>
                ) : (
                  <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-success)', marginTop: '4px' }}>
                    Note: Digital Doctor consultations generate a Kiosk Registration ID for self-service AI consultation.
                  </p>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-3)' }}>
                <Input
                  label={t('frontOffice.firstName')}
                  name="first_name"
                  required
                  value={formData.first_name}
                  onChange={handleChange}
                />
                <Input
                  label={t('frontOffice.lastName')}
                  name="last_name"
                  required
                  value={formData.last_name}
                  onChange={handleChange}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-3)' }}>
                <Input
                  label={t('frontOffice.dob')}
                  name="date_of_birth"
                  type="date"
                  required
                  value={formData.date_of_birth}
                  onChange={handleChange}
                />
                <Select
                  label={t('frontOffice.gender')}
                  name="gender"
                  value={formData.gender}
                  onChange={handleChange}
                  options={[
                    { value: 'Male', label: 'Male' },
                    { value: 'Female', label: 'Female' },
                    { value: 'Other', label: 'Other' },
                  ]}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-3)' }}>
                <Input
                  label={t('frontOffice.phone')}
                  name="contact_phone"
                  required
                  value={formData.contact_phone}
                  onChange={handleChange}
                />
                <Input
                  label={t('frontOffice.email')}
                  name="contact_email"
                  type="email"
                  value={formData.contact_email}
                  onChange={handleChange}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-3)' }}>
                <Select
                  label={t('frontOffice.department')}
                  name="department_id"
                  value={formData.department_id}
                  onChange={handleChange}
                  options={departments.map((d) => ({ value: d.id, label: d.name }))}
                />
                <Select
                  label={t('frontOffice.assignedDoctor')}
                  name="assigned_doctor_id"
                  value={formData.assigned_doctor_id}
                  onChange={handleChange}
                  options={doctors.map((d) => ({ value: d.id, label: `${d.full_name} (${d.specialization})` }))}
                />
              </div>

              {formData.consultation_type === 'DIGITAL_DOCTOR' && (
                <Input
                  label={t('frontOffice.secPin')}
                  name="secondary_verification_pin"
                  hint="Demo PIN or birth year required at Kiosk to prevent unauthorized medical record disclosure"
                  value={formData.secondary_verification_pin}
                  onChange={handleChange}
                />
              )}

              <div style={{ marginTop: 'var(--spacing-4)' }}>
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isSubmitting}
                  style={{ width: '100%' }}
                >
                  {t('frontOffice.registerBtn')}
                </Button>
              </div>
            </form>
          </div>
        </div>

        {/* Recent Registrations Table */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Recent Registrations</h3>
          </div>
          <div className="card-body">
            <DataTable
              columns={columns}
              data={registrations}
              pageSize={6}
            />
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {confirmationData && (
        <Modal
          isOpen={!!confirmationData}
          onClose={() => setConfirmationData(null)}
          title={t('frontOffice.successTitle')}
          footer={
            <Button variant="primary" onClick={() => setConfirmationData(null)}>
              Done
            </Button>
          }
        >
          <div style={{ textAlign: 'center', padding: 'var(--spacing-4) 0' }}>
            <div style={{ fontSize: '48px', color: 'var(--color-success)', marginBottom: 'var(--spacing-2)' }}>✓</div>
            <h3>{confirmationData.patient_full_name}</h3>
            <p style={{ margin: '4px 0 16px' }}>MRN: <strong>{confirmationData.patient_mrn}</strong></p>

            <div style={{ background: 'var(--color-bg-base)', padding: 'var(--spacing-4)', borderRadius: 'var(--border-radius-md)', marginBottom: 'var(--spacing-4)' }}>
              <div style={{ fontSize: 'var(--font-size-xs)', textTransform: 'uppercase', color: 'var(--color-text-muted)', fontWeight: 700 }}>
                {confirmationData.consultation_type === 'DIRECT_DOCTOR' ? 'HIMS Ticket Number' : 'Kiosk Registration ID'}
              </div>
              <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-primary)', letterSpacing: '0.05em' }}>
                {confirmationData.registration_number}
              </div>
            </div>

            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
              {confirmationData.message}
            </p>
          </div>
        </Modal>
      )}
    </div>
  );
}

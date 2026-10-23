const API_BASE = '/api/v1';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = { ...options.headers };

  // Attach token if present: check kiosk session token first, then staff token
  const kioskToken = sessionStorage.getItem('dd_kiosk_token');
  const staffToken = localStorage.getItem('dd_staff_token');

  if (kioskToken) {
    headers['Authorization'] = `Bearer ${kioskToken}`;
  } else if (staffToken) {
    headers['Authorization'] = `Bearer ${staffToken}`;
  }

  // Handle JSON vs FormData
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'Network request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      errorDetail = response.statusText || errorDetail;
    }
    const error = new Error(errorDetail);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

export const api = {
  // Health
  getHealth: () => fetch('/health').then(r => r.json()),

  // Auth
  staffLogin: (username, password) =>
    request('/auth/staff/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  getStaffMe: () => request('/auth/staff/me'),

  // Front Office
  getDepartments: () => request('/front-office/departments'),
  getDoctors: (deptId) => request(`/front-office/doctors${deptId ? `?department_id=${deptId}` : ''}`),
  registerPatient: (data) =>
    request('/front-office/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getRegistrations: (type) =>
    request(`/front-office/registrations${type ? `?consultation_type=${type}` : ''}`),

  // Kiosk
  kioskLookup: (registration_number) =>
    request('/kiosk/lookup', {
      method: 'POST',
      body: JSON.stringify({ registration_number }),
    }),
  kioskVerify: (registration_number, verification_factor) =>
    request('/kiosk/verify', {
      method: 'POST',
      body: JSON.stringify({ registration_number, verification_factor }),
    }),
  createOrResumeSession: (registration_number, existing_session_id, language_preference) =>
    request('/kiosk/session/create-or-resume', {
      method: 'POST',
      body: JSON.stringify({
        registration_number,
        existing_session_id,
        language_preference,
      }),
    }),
  closeSession: (session_id, reason) =>
    request('/kiosk/session/close', {
      method: 'POST',
      body: JSON.stringify({ session_id, reason }),
    }),

  // Consultations & AI
  sendConsultationMessage: (session_id, message, language) =>
    request('/consultations/message', {
      method: 'POST',
      body: JSON.stringify({ session_id, message, language }),
    }),
  getSessionMessages: (session_id) =>
    request(`/consultations/${session_id}/messages`),

  // Clinical Records
  getSessionClinicalHistory: (session_id) =>
    request(`/clinical-records/session/${session_id}/history`),

  // Documents
  uploadMedicalDocument: (sessionId, file, docType = 'Medical Report') => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('document_type', docType);
    formData.append('file', file);
    return request('/documents/upload', {
      method: 'POST',
      body: formData,
    });
  },
  getSessionDocuments: (session_id) =>
    request(`/documents/session/${session_id}`),

  // Clinician Review
  getReviewQueue: () => request('/clinician-review/queue'),
  executeReviewAction: (itemType, itemId, action, notes, rejectionReason) =>
    request(`/clinician-review/action/${itemType}/${itemId}`, {
      method: 'POST',
      body: JSON.stringify({
        action,
        notes,
        rejection_reason: rejectionReason,
      }),
    }),

  // Audit Logs
  getAuditLogs: (limit = 50, eventType = null) =>
    request(`/audit/logs?limit=${limit}${eventType ? `&event_type=${eventType}` : ''}`),
};

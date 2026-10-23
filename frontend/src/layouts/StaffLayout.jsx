import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useI18n } from '../i18n';
import { LanguageSwitcher } from '../components/common/StatusBadge';

export function StaffLayout() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const currentUser = JSON.parse(localStorage.getItem('dd_staff_user') || '{}');

  const handleLogout = () => {
    localStorage.removeItem('dd_staff_token');
    localStorage.removeItem('dd_staff_user');
    navigate('/staff/login');
  };

  return (
    <div className="staff-shell">
      {/* Sidebar */}
      <aside className="staff-sidebar">
        <div className="sidebar-header">
          <div style={{ fontSize: '24px' }}>⚕️</div>
          <h2>Digital Doctor</h2>
        </div>

        <nav className="sidebar-nav">
          <NavLink
            to="/staff"
            end
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            📊 {t('staff.overview')}
          </NavLink>
          <NavLink
            to="/front-office"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            🏥 Front Office Intake
          </NavLink>
          <NavLink
            to="/kiosk"
            target="_blank"
            className="nav-link"
          >
            🖥️ Open Kiosk Mode ↗
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <div>{t('app.hospitalName')}</div>
          <div style={{ marginTop: '4px' }}>Staff Operations Portal</div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="staff-content-area">
        <header className="staff-topbar">
          <div style={{ fontWeight: 600, fontSize: 'var(--font-size-lg)' }}>
            Hospital Clinician Management Console
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-4)' }}>
            <LanguageSwitcher />

            <div className="staff-user-chip">
              <div className="staff-avatar">
                {currentUser.full_name ? currentUser.full_name[0] : 'S'}
              </div>
              <div>
                <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600 }}>
                  {currentUser.full_name || 'Staff User'}
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                  {currentUser.role || 'DOCTOR'}
                </div>
              </div>
            </div>

            <button
              className="btn btn-secondary"
              style={{ minHeight: '36px', padding: '4px 12px' }}
              onClick={handleLogout}
            >
              {t('staff.logout')}
            </button>
          </div>
        </header>

        <main className="staff-page-body">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

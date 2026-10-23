import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/forms/Input';
import { api } from '../../api/client';
import { useToast } from '../../components/notifications/ToastProvider';

export function StaffLogin() {
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [username, setUsername] = useState('dr.anand');
  const [password, setPassword] = useState('DoctorDemo2026!');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const data = await api.staffLogin(username, password);
      localStorage.setItem('dd_staff_token', data.access_token);
      localStorage.setItem('dd_staff_user', JSON.stringify({
        username: data.username,
        full_name: data.full_name,
        role: data.role,
        doctor_id: data.doctor_id,
      }));
      addToast(`Welcome, ${data.full_name}`, 'success');
      navigate('/staff');
    } catch (err) {
      addToast(err.message || 'Login failed', 'danger');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="kiosk-shell" style={{ justifyContent: 'center', alignItems: 'center' }}>
      <div className="card" style={{ width: '100%', maxWidth: '440px', padding: 'var(--spacing-8)' }}>
        <div style={{ textAlign: 'center', marginBottom: 'var(--spacing-6)' }}>
          <div style={{ fontSize: '40px', marginBottom: '8px' }}>🏥</div>
          <h2>Staff Portal Login</h2>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
            Digital Doctor Clinical & Administrative Operations
          </p>
        </div>

        <form onSubmit={handleLogin}>
          <Input
            label="Staff Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <div style={{ marginTop: 'var(--spacing-6)' }}>
            <Button
              type="submit"
              variant="primary"
              style={{ width: '100%' }}
              isLoading={isLoading}
            >
              Sign In to Dashboard &rarr;
            </Button>
          </div>
        </form>

        <div style={{ marginTop: 'var(--spacing-6)', padding: 'var(--spacing-3)', background: 'var(--color-bg-base)', borderRadius: 'var(--border-radius-sm)', fontSize: '11px', color: 'var(--color-text-muted)' }}>
          <div><strong>Demo Staff Accounts (Password: <code>DoctorDemo2026!</code>):</strong></div>
          <div>&bull; <code>dr.anand</code> (Doctor - Internal Medicine)</div>
          <div>&bull; <code>dr.priya</code> (Doctor - Cardiology)</div>
          <div>&bull; <code>admin</code> (System Administrator)</div>
          <div>&bull; <code>frontoffice</code> (Reception Staff)</div>
        </div>
      </div>
    </div>
  );
}

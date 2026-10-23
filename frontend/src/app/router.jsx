import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { KioskWelcome } from '../features/kiosk/KioskWelcome';
import { KioskVerify } from '../features/kiosk/KioskVerify';
import { KioskConsultation } from '../features/kiosk/KioskConsultation';
import { FrontOfficeRegistration } from '../features/front-office/FrontOfficeRegistration';
import { StaffDashboard } from '../features/administration/StaffDashboard';
import { StaffLogin } from '../features/administration/StaffLogin';
import { StaffLayout } from '../layouts/StaffLayout';

// Protected staff route wrapper
function ProtectedStaffRoute({ children }) {
  const token = localStorage.getItem('dd_staff_token');
  if (!token) {
    return <Navigate to="/staff/login" replace />;
  }
  return children;
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/kiosk" replace />,
  },
  {
    path: '/kiosk',
    element: <KioskWelcome />,
  },
  {
    path: '/kiosk/verify',
    element: <KioskVerify />,
  },
  {
    path: '/kiosk/consultation',
    element: <KioskConsultation />,
  },
  {
    path: '/staff/login',
    element: <StaffLogin />,
  },
  {
    path: '/staff',
    element: (
      <ProtectedStaffRoute>
        <StaffLayout />
      </ProtectedStaffRoute>
    ),
    children: [
      {
        index: true,
        element: <StaffDashboard />,
      },
    ],
  },
  {
    path: '/front-office',
    element: (
      <ProtectedStaffRoute>
        <StaffLayout />
      </ProtectedStaffRoute>
    ),
    children: [
      {
        index: true,
        element: <FrontOfficeRegistration />,
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/kiosk" replace />,
  },
]);

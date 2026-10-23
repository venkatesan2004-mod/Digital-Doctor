import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// External CSS stylesheets in structured hierarchy (NO inline styles, NO utility frameworks)
import './styles/tokens.css';
import './styles/global.css';
import './styles/layout.css';
import './styles/components.css';
import './styles/pages.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

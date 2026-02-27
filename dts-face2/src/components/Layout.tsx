// src/components/Layout.tsx
import React, { type ReactNode } from 'react';
import '../styles/global.css'; // Import global styles

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="app-container">
      <header className="app-header">
        <div className="app-header-inner">
          {/* Logo/title area */}
          <h1>
            <span aria-hidden="true" style={{ marginRight: '0.35rem', opacity: 0.8 }}>📈</span>
            DTS Dashboard
          </h1>
          {/* Live badge */}
          <span className="header-badge" role="status" aria-label="Live data">
            <span className="header-dot" aria-hidden="true"></span>
            Live
          </span>
        </div>
      </header>

      <main className="app-main" role="main">
        {children}
      </main>

      <footer className="app-footer" role="contentinfo">
        <p style={{ margin: 0 }}>
          &copy; 2026 DTS Project &middot; All rights reserved.
        </p>
      </footer>
    </div>
  );
};

export default Layout;

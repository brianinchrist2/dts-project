// src/components/LoadingSpinner.tsx
import React from 'react';
import '../styles/components.css'; // Import spinner specific styles

const LoadingSpinner: React.FC = () => {
  return (
    <div className="loading-indicator">
      <div className="loading-spinner"></div>
      <span style={{ marginLeft: '10px', color: 'var(--secondary-color)' }}>Loading...</span>
    </div>
  );
};

export default LoadingSpinner;

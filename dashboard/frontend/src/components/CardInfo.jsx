import React from 'react';

/**
 * CardInfo component - Displays information in a card format
 * This is a minimal implementation to fix build issues
 */
const CardInfo = ({ title, children, className = '', icon }) => {
  return (
    <div className={`bg-white rounded-xl shadow p-4 ${className}`}>
      {title && (
        <div className="flex items-center gap-2 mb-3">
          {icon && <span className="text-primary">{icon}</span>}
          <h3 className="font-medium text-text">{title}</h3>
        </div>
      )}
      <div>{children}</div>
    </div>
  );
};

export default CardInfo;

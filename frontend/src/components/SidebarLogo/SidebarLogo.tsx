import React from 'react';

export type AppStatus = 'active' | 'paused' | 'error';

interface SidebarLogoProps {
  status: AppStatus;
}

export const SidebarLogo: React.FC<SidebarLogoProps> = ({ status }) => {
  const getStyles = () => {
    switch (status) {
      case 'active':
        return {
          stroke: '#00C98F',
          dotVisible: true,
          dotColor: '#00C98F',
          filter: 'drop-shadow(0 0 5px rgba(0,201,143,0.45))',
          opacity: 1
        };
      case 'error':
        return {
          stroke: '#E74C3C',
          dotVisible: true,
          dotColor: '#E74C3C',
          filter: 'drop-shadow(0 0 5px rgba(231,76,60,0.45))',
          opacity: 1
        };
      case 'paused':
      default:
        return {
          stroke: '#4A4A5A',
          dotVisible: false,
          dotColor: '#4A4A5A',
          filter: 'none',
          opacity: 0.45
        };
    }
  };

  const styles = getStyles();

  return (
    <div style={{ transition: 'all 300ms ease-out', opacity: styles.opacity }}>
      <svg 
        viewBox="0 0 28 28" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg" 
        style={{ width: '28px', height: '28px', filter: styles.filter, transition: 'filter 300ms ease-out' }}
      >
        <rect 
          x="1" 
          y="1" 
          width="26" 
          height="26" 
          rx="6" 
          fill="#0A0A0A" 
          stroke="#1A2030" 
          strokeWidth="0.5" 
        />
        <path 
          d="M7 14h5l2-5 2 10 2-5h3" 
          stroke={styles.stroke} 
          strokeWidth="1.5" 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          style={{ transition: 'stroke 300ms ease-out' }}
        />
        {styles.dotVisible && (
          <circle 
            cx="22" 
            cy="6" 
            r="2.5" 
            fill={styles.dotColor}
            style={{ transition: 'fill 300ms ease-out' }}
          />
        )}
      </svg>
    </div>
  );
};

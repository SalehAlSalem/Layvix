import React, { useMemo } from "react";
import "./ActivityStrip.css";

interface ActivityStripProps {
  wpmHistory: number[]; // Using this as latency history as per context
}

export const ActivityStrip: React.FC<ActivityStripProps> = ({ wpmHistory }) => {
  // Generate SVG path string from array of numbers
  const { pathData, areaData, referenceLineY } = useMemo(() => {
    if (!wpmHistory || wpmHistory.length === 0) {
      return { pathData: "", areaData: "", referenceLineY: null };
    }

    const width = 1000;
    const height = 120;
    // Base max value on latency, ensure at least 10ms scale so 5ms line is visible
    const maxVal = Math.max(...wpmHistory, 10);
    const stepX = width / (Math.max(wpmHistory.length - 1, 1));

    const points = wpmHistory.map((val, index) => {
      const x = index * stepX;
      // Invert Y because SVG 0,0 is top-left
      const y = height - (val / maxVal) * height;
      return { x, y };
    });

    const path = points.reduce((acc, point, i) => {
      if (i === 0) return `M ${point.x},${point.y}`;
      return `${acc} L ${point.x},${point.y}`;
    }, "");

    const area = `${path} L ${width},${height} L 0,${height} Z`;
    
    const referenceLineY = height - (5 / maxVal) * height; // 5ms threshold

    return { pathData: path, areaData: area, referenceLineY };
  }, [wpmHistory]);

  return (
    <div className="activity-container">
      <div className="activity-y-axis-label">latency ms</div>
      <svg
        className="activity-svg"
        viewBox="0 0 1000 120"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="pulse-gradient" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="rgba(0, 201, 143, 0.15)" />
            <stop offset="100%" stopColor="rgba(0, 201, 143, 0)" />
          </linearGradient>
        </defs>
        
        {/* 5ms Threshold Line */}
        {referenceLineY !== null && (
          <line 
            x1="0" 
            y1={referenceLineY} 
            x2="1000" 
            y2={referenceLineY} 
            className="reference-line" 
          />
        )}
        
        {areaData && <path d={areaData} className="activity-gradient" />}
        {pathData && <path d={pathData} className="activity-pulse-path" />}
      </svg>
    </div>
  );
};

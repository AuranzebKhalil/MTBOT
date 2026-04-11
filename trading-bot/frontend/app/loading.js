"use client";
import React from "react";
import Image from "next/image";

export default function Loading() {
  return (
    <div className="auralith-loading-overlay">
      <div className="auralith-loading-content">
        <div className="auralith-quantum-spinner">
          <div className="spinner-ring inner"></div>
          <div className="spinner-ring outer"></div>
          <div className="spinner-core">
            <Image 
              src="/logo/AuraLithLogo.png" 
              alt="Logo" 
              width={40} 
              height={40} 
              style={{ filter: 'drop-shadow(0 0 10px var(--primary-glow))' }}
            />
          </div>
        </div>
        <div className="auralith-shimmer-text">
          AURALITH<span>INTELLIGENCE</span>
        </div>
        <div className="sync-status">SYNCHRONIZING QUANTUM CORE...</div>
      </div>

      <style jsx>{`
        .auralith-loading-overlay {
          position: fixed;
          top: 0;
          left: 0;
          width: 100vw;
          height: 100vh;
          background: var(--background);
          display: flex;
          alignItems: center;
          justifyContent: center;
          z-index: 9999;
          backdrop-filter: blur(20px);
        }

        .auralith-loading-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 32px;
        }

        .auralith-quantum-spinner {
          position: relative;
          width: 120px;
          height: 120px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .spinner-ring {
          position: absolute;
          border-radius: 50%;
          border: 2px solid transparent;
        }

        .spinner-ring.outer {
          width: 100%;
          height: 100%;
          border-top-color: var(--primary);
          border-bottom-color: var(--accent);
          animation: spin 1.5s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
        }

        .spinner-ring.inner {
          width: 70%;
          height: 70%;
          border-left-color: var(--primary);
          border-right-color: var(--accent);
          animation: spin-reverse 1s linear infinite;
          opacity: 0.6;
        }

        .spinner-core {
          font-family: var(--font-main);
          font-size: 32px;
          font-weight: 900;
          color: #fff;
          text-shadow: 0 0 20px var(--primary-glow);
          animation: pulse 1s ease-in-out infinite alternate;
        }

        .auralith-shimmer-text {
          font-family: var(--font-main);
          font-size: 28px;
          font-weight: 900;
          color: #fff;
          letter-spacing: 8px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
        }

        .auralith-shimmer-text span {
          font-size: 10px;
          letter-spacing: 4px;
          color: var(--text-sub);
          font-weight: 700;
        }

        .sync-status {
          font-family: var(--font-mono);
          font-size: 10px;
          color: var(--primary);
          letter-spacing: 2px;
          opacity: 0.8;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        @keyframes spin-reverse {
          to { transform: rotate(-360deg); }
        }

        @keyframes pulse {
          from { transform: scale(0.95); opacity: 0.8; }
          to { transform: scale(1.05); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

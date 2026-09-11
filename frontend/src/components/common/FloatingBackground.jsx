import React from 'react';
import './FloatingBackground.css';

/**
 * FloatingBackground
 * Renders rich, high-visibility floating ambient objects in the background:
 * 1. Radiant breathing ambient orbs (emerald aurora, harvest gold, sage dew)
 * 2. Drifting agricultural & botanical motifs:
 *    - Floating leaves (broad leaf, neem/herbal leaf, slender paddy leaf, fluttering autumn leaf)
 *    - Sprouting seedlings & plant buds
 *    - Golden wheat stalks, paddy ears, and grain kernels
 *    - Luminescent harvest motes, pollen sparks, and glowing fireflies
 * 
 * Hardware-accelerated CSS translate3d transforms (pointer-events: none, 0 performance impact).
 */
export const FloatingBackground = () => {
  return (
    <div className="ambient-floating-bg" aria-hidden="true">
      {/* Radiant Glowing Ambient Blobs with Rich Saturation */}
      <div className="ambient-orb orb-primary" />
      <div className="ambient-orb orb-gold" />
      <div className="ambient-orb orb-sage" />
      <div className="ambient-orb orb-warm" />

      {/* Floating Agricultural & Botanical Motifs */}
      <div className="floating-objects-container">
        {/* Leaf 1: Broad tropical/farm leaf drifting diagonally from bottom-left */}
        <div className="floating-object drift-leaf-1">
          <svg viewBox="0 0 24 24" width="34" height="34" fill="currentColor">
            <path d="M17 8C8 10 5.9 16.17 3.82 21.34L5.71 22l1-2.3A4.49 4.49 0 0 0 8 20C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75C7 8 17 8 17 8z" />
          </svg>
        </div>

        {/* Leaf 2: Herbal / Neem compound leaf swaying in upper right */}
        <div className="floating-object drift-leaf-2">
          <svg viewBox="0 0 24 24" width="30" height="30" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
          </svg>
        </div>

        {/* Leaf 3: Slender paddy / wheat leaf on mid-right */}
        <div className="floating-object drift-leaf-3">
          <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
            <path d="M2 12C2 6.5 6.5 2 12 2c4 0 7 2 8.5 5 1.5 3 .5 7-2.5 10-3 3-7 4-11 4C4 21 2 17 2 12zm10-8c-4.4 0-8 3.6-8 8 0 3.2 1.4 5.9 3.5 7.1C9.6 15 12 9.5 16 7c-1.3-1.8-3.4-3-6-3z" />
          </svg>
        </div>

        {/* Leaf 4: Gentle curved leaf drifting across top-left */}
        <div className="floating-object drift-leaf-4">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
            <path d="M19.5 3.5L18 2l-1.5 1.5C12.5 7.5 7 13 7 18c0 2.76 2.24 5 5 5s5-2.24 5-5c0-5.5 5.5-11 7-12.5l-4.5-2z" />
          </svg>
        </div>

        {/* Leaf 5: Golden amber leaf floating near bottom-center */}
        <div className="floating-object drift-leaf-5">
          <svg viewBox="0 0 24 24" width="30" height="30" fill="currentColor">
            <path d="M17 8C8 10 5.9 16.17 3.82 21.34L5.71 22l1-2.3A4.49 4.49 0 0 0 8 20C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75C7 8 17 8 17 8z" />
          </svg>
        </div>

        {/* Sprout 1: Two-leaf agricultural sprout on mid-left */}
        <div className="floating-object drift-sprout-1">
          <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
            <path d="M12 22v-7a6 6 0 0 0-6-6H3a10 10 0 0 1 10 10v3h-1zm2-10a5 5 0 0 1 5-5h3a9 9 0 0 0-9 9v-4z" />
          </svg>
        </div>

        {/* Sprout 2: Seedling rising near top-center */}
        <div className="floating-object drift-sprout-2">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
            <path d="M12 3v10m0 0c-3.3 0-6-2.7-6-6h2a4 4 0 0 1 4 4zm0 0c3.3 0 6-2.7 6-6h-2a4 4 0 0 0-4 4zm0 0v8" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
          </svg>
        </div>

        {/* Sprout 3: Flourishing plant seedling on right */}
        <div className="floating-object drift-sprout-3">
          <svg viewBox="0 0 24 24" width="30" height="30" fill="currentColor">
            <path d="M12 22v-7a6 6 0 0 0-6-6H3a10 10 0 0 1 10 10v3h-1zm2-10a5 5 0 0 1 5-5h3a9 9 0 0 0-9 9v-4z" />
          </svg>
        </div>

        {/* Golden Harvest Grain 1: Wheat ear on right side */}
        <div className="floating-object drift-grain-1">
          <svg viewBox="0 0 24 24" width="26" height="26" fill="currentColor">
            <ellipse cx="12" cy="7" rx="3.5" ry="5" transform="rotate(25 12 7)" />
            <ellipse cx="9" cy="13" rx="3.5" ry="5" transform="rotate(-25 9 13)" />
            <ellipse cx="15" cy="13" rx="3.5" ry="5" transform="rotate(25 15 13)" />
            <line x1="12" y1="5" x2="12" y2="22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>

        {/* Golden Harvest Grain 2: Sunlit grain ear on left side */}
        <div className="floating-object drift-grain-2">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
            <ellipse cx="12" cy="12" rx="4.5" ry="10" transform="rotate(-35 12 12)" />
          </svg>
        </div>

        {/* Golden Harvest Grain 3: Grain cluster drifting across bottom */}
        <div className="floating-object drift-grain-3">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <ellipse cx="12" cy="12" rx="4" ry="9" transform="rotate(40 12 12)" />
          </svg>
        </div>

        {/* Golden Harvest Grain 4: Wheat seed near top-right */}
        <div className="floating-object drift-grain-4">
          <svg viewBox="0 0 24 24" width="26" height="26" fill="currentColor">
            <ellipse cx="12" cy="7" rx="3" ry="5" transform="rotate(20 12 7)" />
            <ellipse cx="12" cy="15" rx="3" ry="5" transform="rotate(-20 12 15)" />
            <line x1="12" y1="4" x2="12" y2="21" stroke="currentColor" strokeWidth="2" />
          </svg>
        </div>

        {/* Glowing Fireflies & Harvest Pollen Motes (High Visibility) */}
        <div className="floating-object drift-mote-1" />
        <div className="floating-object drift-mote-2" />
        <div className="floating-object drift-mote-3" />
        <div className="floating-object drift-mote-4" />
        <div className="floating-object drift-mote-5" />
        <div className="floating-object drift-mote-6" />
      </div>
    </div>
  );
};

import React from "react";
import { Target, Zap, Activity, TrendingUp, BarChart3, Globe } from "lucide-react";

const flagMapping = {
  'USD': 'us', 'EUR': 'eu', 'JPY': 'jp', 'GBP': 'gb', 'AUD': 'au', 'CHF': 'ch', 'CAD': 'ca', 'NZD': 'nz',
  'DKK': 'dk', 'HKD': 'hk', 'HUF': 'hu', 'NOK': 'no', 'PLN': 'pl', 'SEK': 'se', 'SGD': 'sg', 'TRY': 'tr', 
  'ZAR': 'za', 'CNH': 'cn', 'MXN': 'mx', 'DKK': 'dk', 'ILS': 'il', 'KRW': 'kr', 'THB': 'th'
};

const cryptoLogos = {
  'BTC': 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/btc.png',
  'ETH': 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/eth.png',
  'SOL': 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/sol.png',
  'BNB': 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/bnb.png',
  'ETC': 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/etc.png',
  'XRP': 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/xrp.png',
  'ADA': 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/ada.png'
};

export default function AssetIcon({ symbol, size = 18 }) {
  const s = symbol.toUpperCase();
  
  // 1. Crypto Handling
  if (s.includes("BTC") || s.includes("ETH") || s.includes("SOL") || s.includes("BNB") || s.includes("ETC")) {
    const coin = s.replace("USD", "").replace("USDT", "").trim();
    return (
      <div style={{ width: size * 1.5, height: size * 1.5, borderRadius: '50%', overflow: 'hidden', background: 'var(--divider)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <img 
          src={cryptoLogos[coin] || `https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/${coin.toLowerCase()}.png`}
          alt={coin}
          width="100%"
          height="100%"
          onError={(e) => { e.currentTarget.src = 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/generic.png'; }}
          style={{ objectFit: 'contain' }}
        />
      </div>
    );
  }

  // 2. Gold / Metals (Realistic Gold Bar + Pair Flag)
  if (s.includes("XAU") || s.includes("GOLD")) {
    const isPair = s.includes("USD") || s.length > 3;
    return (
      <div style={{ position: 'relative', width: isPair ? size * 2.5 : size * 1.5, height: size * 1.5, display: 'flex', alignItems: 'center' }}>
        {/* Real Gold Bar Asset */}
        <div style={{ 
          width: size * 1.5, height: size * 1.5, borderRadius: '50%', overflow: 'hidden', 
          zIndex: 2, border: '2px solid var(--bg-card)', position: 'absolute', left: 0,
          background: 'linear-gradient(135deg, #fceabb 0%, #f8b500 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '2px 0 8px rgba(0,0,0,0.3)'
        }}>
          <img 
            src="https://img.icons8.com/color/96/gold-bars.png" 
            style={{ width: '80%', height: '80%', objectFit: 'contain' }}
            alt="Gold"
          />
        </div>
        {/* USD Quote Flag (Only if it's a pair) */}
        {isPair && (
          <div style={{ 
            width: size * 1.3, height: size * 1.3, borderRadius: '50%', overflow: 'hidden', 
            zIndex: 1, border: '1px solid var(--border)', position: 'absolute', left: size * 0.9,
            opacity: 0.9
          }}>
            <img 
              src="https://flagcdn.com/w80/us.png" 
              style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
              alt="USD"
            />
          </div>
        )}
      </div>
    );
  }

  // 3. Forex Pairs (6 characters)
  if (s.length === 6 && !s.includes("BTC") && !s.includes("ETH")) {
    const base = s.substring(0, 3);
    const quote = s.substring(3, 6);
    const baseFlag = flagMapping[base] || 'un';
    const quoteFlag = flagMapping[quote] || 'un';

    return (
      <div style={{ position: 'relative', width: size * 2.2, height: size * 1.4, display: 'flex', alignItems: 'center' }}>
        {/* Base Currency Flag (Front) */}
        <div style={{ 
          width: size * 1.3, height: size * 1.3, borderRadius: '50%', overflow: 'hidden', 
          zIndex: 2, border: '2px solid var(--bg-card)', position: 'absolute', left: 0,
          boxShadow: '2px 0 5px rgba(0,0,0,0.2)'
        }}>
          <img 
            src={`https://flagcdn.com/w80/${baseFlag}.png`} 
            style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
            alt={base}
          />
        </div>
        {/* Quote Currency Flag (Back) */}
        <div style={{ 
          width: size * 1.3, height: size * 1.3, borderRadius: '50%', overflow: 'hidden', 
          zIndex: 1, border: '1px solid var(--border)', position: 'absolute', left: size * 0.7,
          opacity: 0.9
        }}>
          <img 
            src={`https://flagcdn.com/w80/${quoteFlag}.png`} 
            style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
            alt={quote}
          />
        </div>
      </div>
    );
  }

  // Fallback to generic lucide icons if no mapping found
  if (s.includes("USD")) return <Globe size={size} color="#007aff" />;
  
  return (
    <div style={{ width: size, height: size, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Target size={size} color="var(--text-sub)" />
    </div>
  );
}

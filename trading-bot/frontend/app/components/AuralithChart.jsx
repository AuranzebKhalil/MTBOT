"use client";
import React, { useEffect, useRef, useState, useMemo } from "react";
import { createChart, ColorType } from "lightweight-charts";
import { 
  Zap, 
  Settings2, 
  Eye, 
  EyeOff, 
  MousePointer2, 
  Layers
} from "lucide-react";
import { useBot } from "./BotContext";
import { useTheme } from "./ThemeContext";

/**
 * Institutional Zone Renderer
 */
class ZonePrimitivePaneRenderer {
  constructor(source) {
    this._source = source;
  }
  draw(target) {
    target.useBitmapCoordinateSpace((scope) => {
      const ctx = scope.context;
      const chart = this._source._chart;
      const series = this._source._series;
      if (!chart || !series) return;

      const timeScale = chart.timeScale();
      const x1 = timeScale.timeToCoordinate(this._source._opt.time1);
      if (x1 === null) return;

      let x2;
      if (this._source._opt.time2) {
        let mapped = timeScale.timeToCoordinate(this._source._opt.time2);
        x2 = mapped !== null ? mapped : timeScale.width();
      } else {
        x2 = timeScale.width();
      }

      const y1 = series.priceToCoordinate(this._source._opt.price1);
      const y2 = series.priceToCoordinate(this._source._opt.price2);

      if (y1 === null || y2 === null) return;

      const pxRatio = scope.horizontalPixelRatio;
      const pyRatio = scope.verticalPixelRatio;

      const rectX = Math.min(x1, x2) * pxRatio;
      const rectY = Math.min(y1, y2) * pyRatio;
      const rectW = Math.max(1, Math.abs(x2 - x1)) * pxRatio;
      const rectH = Math.max(1, Math.abs(y2 - y1)) * pyRatio;

      ctx.fillStyle = this._source._opt.color;
      ctx.fillRect(rectX, rectY, rectW, rectH);

      if (this._source._opt.border) {
        ctx.strokeStyle = this._source._opt.color;
        ctx.lineWidth = 1 * pxRatio;
        ctx.strokeRect(rectX, rectY, rectW, rectH);
      }

      if (this._source._opt.label && rectW > 30 * pxRatio && rectH > 20 * pyRatio) {
        ctx.fillStyle = this._source._theme === "dark" ? "rgba(255,255,255,0.4)" : "rgba(0,0,0,0.5)";
        ctx.font = `bold ${8 * pyRatio}px 'Inter', sans-serif`;
        ctx.textAlign = "left";
        ctx.fillText(this._source._opt.label, rectX + 6 * pxRatio, rectY + 12 * pyRatio);
      }
    });
  }
}

class ZonePrimitivePaneView {
  constructor(source) { this._source = source; }
  update() {}
  renderer() { return new ZonePrimitivePaneRenderer(this._source); }
}

class ZonePrimitive {
  constructor(opt, theme) {
    this._opt = opt;
    this._theme = theme;
    this._paneViews = [new ZonePrimitivePaneView(this)];
  }
  attached({ chart, series, requestUpdate }) {
    this._chart = chart;
    this._series = series;
    this._requestUpdate = requestUpdate;
  }
  detached() {
    this._chart = null;
    this._series = null;
  }
  updateAllViews() {
    if (this._requestUpdate) this._requestUpdate();
  }
  paneViews() { return this._paneViews; }
}

export default function AuralithChart({ symbol }) {
  const chartContainerRef = useRef();
  const { symbolData, trades } = useBot();
  const { theme } = useTheme();

  const [settings, setSettings] = useState({
    showBOS: true, showFVG: true, showOB: true, showSweeps: true, showSR: true, 
    showTrades: true, showMSS: true, showVolume: true,
  });
  const [showSettings, setShowSettings] = useState(false);
  const [tooltip, setTooltip] = useState(null);

  const symbolState = symbolData[symbol] || {};
  const chartEntries = symbolState.chart || [];
  const overlays = symbolState.overlays || {
    fvg_zones: [], order_blocks: [], sweeps: [], bos_markers: [], support_resistance: [],
    mss_markers: [], breaker_markers: [], volume_zones: []
  };

  const [chartLoaded, setChartLoaded] = useState(false);
  const candlestickSeriesRef = useRef(null);
  const chartRef = useRef(null);
  const overlaysRef = useRef([]);

  const symbolTrades = useMemo(() => trades?.filter((t) => t.symbol === symbol) || [], [trades, symbol]);

  const clearOverlays = () => {
    if (overlaysRef.current) {
      overlaysRef.current.forEach((obj) => {
        if (obj.remove) obj.remove();
        else if (obj.primitive && candlestickSeriesRef.current)
          candlestickSeriesRef.current.detachPrimitive(obj.primitive);
      });
      overlaysRef.current = [];
    }
  };

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: theme === "dark" ? "#848e9c" : "#64748b",
        fontFamily: "'Inter', sans-serif",
      },
      grid: {
        vertLines: { color: theme === "dark" ? "rgba(255, 255, 255, 0.02)" : "rgba(0, 0, 0, 0.03)" },
        horzLines: { color: theme === "dark" ? "rgba(255, 255, 255, 0.02)" : "rgba(0, 0, 0, 0.03)" },
      },
      timeScale: {
        borderColor: theme === "dark" ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.05)",
        timeVisible: true,
      },
      rightPriceScale: {
        borderColor: theme === "dark" ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.05)",
        scaleMargins: { top: 0.15, bottom: 0.15 },
      },
      crosshair: { mode: 1 },
    });

    const upColor = "#32d74b";
    const downColor = "#ff453a";

    const candlestickSeries = chart.addCandlestickSeries({
      upColor, downColor, borderVisible: false, wickUpColor: upColor, wickDownColor: downColor,
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    setChartLoaded(true);

    const resizeObserver = new ResizeObserver((entries) => {
      if (entries.length === 0 || !chartRef.current) return;
      const { width, height } = entries[0].contentRect;
      chartRef.current.applyOptions({ width, height });
    });
    resizeObserver.observe(chartContainerRef.current);

    chart.subscribeCrosshairMove((param) => {
      if (!param.time || param.point === undefined || !param.seriesData.get(candlestickSeries)) {
        setTooltip(null);
        return;
      }
      const data = param.seriesData.get(candlestickSeries);
      if (data) {
        setTooltip({ x: param.point.x, y: param.point.y, price: data.close || data.value, time: param.time });
      }
    });

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [theme]);

  useEffect(() => {
    if (chartLoaded && candlestickSeriesRef.current && chartEntries.length > 0) {
      const uniqueData = Array.from(new Map(chartEntries.map(entry => [entry.time, entry])).values())
        .sort((a, b) => a.time - b.time);
      
      candlestickSeriesRef.current.setData(uniqueData);
      
      // On initial load, fit the content nicely
      if (chartEntries.length < 50) {
         chartRef.current.timeScale().fitContent();
      }
    }
  }, [chartEntries, chartLoaded]);

  useEffect(() => {
    if (!chartLoaded) return;
    clearOverlays();
    const series = candlestickSeriesRef.current;
    if (!series) return;

    if (settings.showSR && overlays.support_resistance) {
       overlays.support_resistance.forEach(lv => {
         const line = series.createPriceLine({
           price: lv.price, color: "rgba(34, 163, 240, 0.2)", lineWidth: 1, lineStyle: 2, title: lv.type.toUpperCase()
         });
         overlaysRef.current.push({ remove: () => series.removePriceLine(line) });
       });
    }

    const rawMarkers = [];
    if (settings.showBOS && overlays.bos_markers) {
       overlays.bos_markers.forEach(m => rawMarkers.push({ 
         time: m.time, 
         position: m.type === "bearish" ? "aboveBar" : "belowBar", 
         color: m.type === "bearish" ? "#ff453a" : "#32d74b", 
         shape: m.type === "bearish" ? "arrowDown" : "arrowUp", 
         text: m.label || "BOS",
         category: "structure"
       }));
    }
    if (settings.showCHoCH && overlays.choch_markers) {
       overlays.choch_markers.forEach(m => rawMarkers.push({ 
         time: m.time, 
         position: m.type === "bearish" ? "aboveBar" : "belowBar", 
         color: m.type === "bearish" ? "#ff453a" : "#32d74b", 
         shape: "circle", 
         text: m.label || "CHoCH",
         category: "structure"
       }));
    }
    if (settings.showSweeps && overlays.sweeps) {
       overlays.sweeps.forEach(s => rawMarkers.push({ 
         time: s.time, 
         position: s.type === "bullish" ? "belowBar" : "aboveBar", 
         color: "#bf5af2", 
         shape: "circle", 
         text: "LIQ",
         category: "liquidity"
       }));
    }
    if (settings.showMSS && overlays.mss_markers) {
       overlays.mss_markers.forEach(m => rawMarkers.push({ 
         time: m.time, 
         position: m.type === "bearish" ? "aboveBar" : "belowBar", 
         color: "#ffd60a", 
         shape: "circle", 
         text: "MSS",
         category: "structure"
       }));
    }
    
    // De-clutter markers: Ensure same category markers are spaced out
    rawMarkers.sort((a, b) => a.time - b.time);
    const uniqueMarkers = [];
    const lastPos = {};
    
    rawMarkers.forEach(m => {
       const key = `${m.category}_${m.text}`;
       if (!lastPos[key] || m.time - lastPos[key] > 300) { // 5 minutes (300s) spacing for same type
          uniqueMarkers.push(m);
          lastPos[key] = m.time;
       }
    });

    const limitedMarkers = uniqueMarkers.slice(-40); 
    series.setMarkers(limitedMarkers);

    if (settings.showPD && overlays.pd_zones) {
        const pd = overlays.pd_zones[overlays.pd_zones.length - 1];
        if (pd) {
            const pLine = series.createPriceLine({ price: pd.premium, color: "rgba(255, 69, 58, 0.15)", lineWidth: 1, lineStyle: 2, title: "PREMIUM" });
            const eqLine = series.createPriceLine({ price: pd.equilibrium, color: "rgba(255, 255, 255, 0.15)", lineWidth: 1, lineStyle: 2, title: "EQ" });
            const dLine = series.createPriceLine({ price: pd.discount, color: "rgba(50, 215, 75, 0.15)", lineWidth: 1, lineStyle: 2, title: "DISCOUNT" });
            overlaysRef.current.push({ remove: () => { 
                series.removePriceLine(pLine); 
                series.removePriceLine(eqLine); 
                series.removePriceLine(dLine); 
            }});
        }
    }

    if (settings.showOB && overlays.order_blocks) {
       overlays.order_blocks.slice(-5).forEach(ob => {
         const primitive = new ZonePrimitive({ 
           time1: ob.time, 
           price1: ob.top, 
           price2: ob.bottom, 
           color: ob.type === "bullish" ? "rgba(50, 215, 75, 0.05)" : "rgba(255, 69, 58, 0.05)", 
           border: true, 
           label: "OB" 
         }, theme);
         series.attachPrimitive(primitive);
         overlaysRef.current.push({ primitive });
       });
    }

    if (settings.showFVG && overlays.fvg_zones) {
      overlays.fvg_zones.slice(-5).forEach(f => {
        const primitive = new ZonePrimitive({ 
          time1: f.time, 
          price1: f.top, 
          price2: f.bottom, 
          color: "rgba(34, 163, 240, 0.04)", 
          border: true, 
          label: "FVG" 
        }, theme);
        series.attachPrimitive(primitive);
        overlaysRef.current.push({ primitive });
      });
    }

    if (settings.showTrades && symbolTrades) {
      symbolTrades.forEach(t => {
        const entry = series.createPriceLine({ price: t.entry_price, color: "#ffd60a", lineWidth: 2, title: "ENTRY" });
        overlaysRef.current.push({ remove: () => series.removePriceLine(entry) });
      });
    }
  }, [overlays, settings, chartLoaded, symbolTrades]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", overflow: "hidden" }}>
      {/* Background with Grid pattern */}
      <div style={{ 
        position: "absolute", inset: 0, opacity: theme === 'dark' ? 0.1 : 0.05, pointerEvents: "none",
        backgroundImage: `radial-gradient(${theme === 'dark' ? "var(--primary)" : "var(--text-sub)"} 1px, transparent 1px)`,
        backgroundSize: '32px 32px'
      }}></div>

      <div style={{ position: "absolute", top: "16px", left: "16px", zIndex: 100, display: "flex", gap: "8px" }}>
        <div style={{ 
          background: "var(--glass-bg)", 
          padding: "8px 14px", 
          borderRadius: "10px", 
          border: "1px solid var(--border)", 
          display: "flex", 
          alignItems: "center", 
          gap: "8px", 
          backdropFilter: "blur(10px)",
          boxShadow: "0 4px 20px rgba(0,0,0,0.05)"
        }}>
          <Zap size={14} color="var(--primary)" />
          <span style={{ fontSize: "11px", fontWeight: "800", color: "var(--text-main)" }}>ALPHA QUANT v4.5</span>
        </div>
        <button 
          onClick={() => setShowSettings(!showSettings)} 
          style={{ 
            background: "var(--glass-bg)", 
            padding: "8px", 
            borderRadius: "10px", 
            border: "1px solid var(--border)", 
            color: "var(--text-secondary)", 
            cursor: "pointer",
            backdropFilter: "blur(10px)",
            boxShadow: "0 4px 20px rgba(0,0,0,0.05)"
          }}
        >
          <Settings2 size={16} />
        </button>
      </div>

      {showSettings && (
        <div className="fade-in" style={{ position: "absolute", top: "60px", left: "16px", zIndex: 110, width: "200px", padding: "20px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "16px", boxShadow: "0 20px 40px rgba(0,0,0,0.4)" }}>
          <div style={{ fontSize: "11px", fontWeight: "800", marginBottom: "16px", color: "var(--primary)" }}>CHART LAYERS</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {Object.keys(settings).map(key => (
              <div key={key} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "10px", color: "var(--text-secondary)", fontWeight: "700" }}>{key.replace("show","").toUpperCase()}</span>
                <button 
                  onClick={() => setSettings(s => ({ ...s, [key]: !s[key]}))} 
                  style={{ 
                    background: "none", 
                    border: "none", 
                    cursor: "pointer", 
                    color: settings[key] ? "var(--primary)" : "var(--divider)" 
                  }}
                >
                  {settings[key] ? <Eye size={14} /> : <EyeOff size={14} />}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Internal Spread Overlay */}
      <div style={{
          position: "absolute",
          top: "16px",
          right: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "2px",
          alignItems: "flex-end",
          pointerEvents: "none",
          zIndex: 100,
          background: theme === 'dark' ? "rgba(0,0,0,0.2)" : "rgba(255,255,255,0.8)",
          padding: "6px 12px",
          borderRadius: "8px",
          border: "1px solid var(--border)",
          backdropFilter: "blur(4px)"
        }}>
          <div style={{ fontSize: "9px", fontWeight: "700", color: "var(--text-secondary)", opacity: 0.7 }}>SPREAD</div>
          <div style={{ fontSize: "11px", fontWeight: "900", color: "var(--text-main)", letterSpacing: "0.5px" }}>0.4 PIP</div>
      </div>

      {tooltip && (
        <div style={{ 
          position: "absolute", 
          top: tooltip.y - 60, 
          left: tooltip.x + 20, 
          zIndex: 120, 
          background: theme === 'dark' ? "rgba(13,17,23,0.9)" : "rgba(255,255,255,0.95)", 
          border: `1px solid ${theme === 'dark' ? "var(--primary)" : "var(--border)"}`, 
          padding: "8px 16px", 
          borderRadius: "10px", 
          pointerEvents: "none", 
          boxShadow: theme === 'dark' ? "0 0 20px var(--primary-light)" : "0 8px 20px rgba(0,0,0,0.1)" 
        }}>
          <div style={{ fontSize: "14px", fontWeight: "900", color: "var(--text-main)" }}>$ {tooltip.price.toLocaleString()}</div>
        </div>
      )}

      <div style={{ 
        position: "absolute", bottom: "16px", right: "16px", zIndex: 100, 
        display: "flex", gap: "16px", 
        background: theme === 'dark' ? "rgba(13, 17, 23, 0.6)" : "rgba(255, 255, 255, 0.8)", 
        padding: "8px 16px", borderRadius: "8px", border: "1px solid var(--border)",
        backdropFilter: "blur(10px)",
        boxShadow: "0 4px 20px rgba(0,0,0,0.1)"
      }}>
         <LegendItem color={theme === 'dark' ? "rgba(50, 215, 75, 0.6)" : "rgba(50, 215, 75, 0.8)"} label="OB ZONE" />
         <LegendItem color={theme === 'dark' ? "rgba(255, 69, 58, 0.6)" : "rgba(255, 69, 58, 0.8)"} label="P/D ZONES" />
         <LegendItem color="#bf5af2" label="LIQUIDITY" isCircle />
      </div>

      <div ref={chartContainerRef} style={{ width: "100%", height: "100%" }} />
    </div>
  );
}

function LegendItem({ color, label, isCircle = false }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
      <div style={{ width: "8px", height: "8px", borderRadius: isCircle ? "50%" : "2px", background: color }}></div>
      <span style={{ fontSize: "9px", color: "var(--text-secondary)", fontWeight: "800" }}>{label}</span>
    </div>
  );
}

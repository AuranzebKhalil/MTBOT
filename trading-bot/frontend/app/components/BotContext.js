"use client";
import React, { createContext, useContext, useState, useEffect } from "react";
import toast from "react-hot-toast";
import { useAuth } from "./AuthContext";
import {
  useGetMultiStatusQuery,
  useGetTradesQuery,
  useGetHistoryQuery,
  useGetRiskQuery,
  useGetEngineConfigQuery,
  useGetStrategySettingsQuery,
  useGetStrategiesQuery,
  useToggleBotMutation,
  useUpdateRiskMutation,
  useUpdateStrategyMutation,
  useAddStrategyMutation,
  useDeleteStrategyMutation,
  useResetHistoryMutation,
  useResetRiskMutation,
  useUpdateSymbolVolumeMutation,
  useDeleteHistoryItemMutation,
  useCloseTradeMutation,
} from "../lib/apiSlice";
import { getApiBaseUrl } from "../lib/config";

const BotContext = createContext();

export function BotProvider({ children }) {
  const { token, logout } = useAuth();

  // RTK Query Hooks
  const { data: multiData } = useGetMultiStatusQuery(undefined, {
    skip: !token,
  });

  const { data: trades = [] } = useGetTradesQuery(undefined, {
    skip: !token,
    pollingInterval: 5000,
  });

  const { data: history = [] } = useGetHistoryQuery(undefined, {
    skip: !token,
    pollingInterval: 30000,
  });

  const { data: customStrategies = [] } = useGetStrategiesQuery(undefined, {
    skip: !token,
    pollingInterval: 30000,
  });

  const { data: riskData } = useGetRiskQuery(undefined, { skip: !token });
  const { data: engineConfig = {} } = useGetEngineConfigQuery(undefined, { skip: !token });
  const { data: strategySettings = {} } = useGetStrategySettingsQuery(undefined, { skip: !token });

  // Mutations
  const [toggleBot] = useToggleBotMutation();
  const [updateRisk] = useUpdateRiskMutation();
  const [updateStrategy] = useUpdateStrategyMutation();
  const [addStrategy] = useAddStrategyMutation();
  const [deleteStrategy] = useDeleteStrategyMutation();
  const [resetHistory] = useResetHistoryMutation();
  const [deleteHistoryItem] = useDeleteHistoryItemMutation();
  const [resetRisk] = useResetRiskMutation();
  const [updateSymbolVolume] = useUpdateSymbolVolumeMutation();
  const [closeTrade] = useCloseTradeMutation();

  // Local state for UI
  const [isEngineSettingsOpen, setIsEngineSettingsOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSidebarHidden, setIsSidebarHidden] = useState(false);
  const [localStrategySettings, setLocalStrategySettings] = useState({});
  const [riskParams, setRiskParams] = useState({
    risk_per_trade: 1,
    max_trades: 5,
    max_daily_trades: 20,
    daily_loss: 5,
    risk_reward_ratio: 1.5,
    // Partial Execution
    partial_execution_enabled: true,
    partial_stage_1_trigger: 60,
    partial_stage_1_close_pct: 50,
    partial_stage_2_trigger: 80,
    partial_stage_2_close_pct: 25,
    trading_mode: "DEMO"
  });

  // Sync server risk data to local state
  useEffect(() => {
    if (riskData) {
      setRiskParams({
        risk_per_trade: (riskData.risk_per_trade || 0.01) * 100,
        max_trades: riskData.max_trades || 5,
        max_daily_trades: riskData.max_daily_trades || 20,
        daily_loss: (riskData.daily_loss_limit || 0.1) * 100,
        risk_reward_ratio: riskData.risk_reward_ratio || 1.5,
        partial_execution_enabled: riskData.partial_execution_enabled ?? true,
        partial_stage_1_trigger: (riskData.partial_stage_1_trigger || 0.6) * 100,
        partial_stage_1_close_pct: (riskData.partial_stage_1_close_pct || 0.5) * 100,
        partial_stage_2_trigger: (riskData.partial_stage_2_trigger || 0.8) * 100,
        partial_stage_2_close_pct: (riskData.partial_stage_2_close_pct || 0.25) * 100,
        trading_mode: riskData.trading_mode || "DEMO"
      });
    }
  }, [riskData]);
  
  // Sync core strategy settings to local state for instant UI responsiveness
  useEffect(() => {
    if (strategySettings && Object.keys(strategySettings).length > 0) {
      setLocalStrategySettings(prev => ({...strategySettings, ...prev}));
    }
  }, [strategySettings]);

  // Derived UI State
  const botStatus = multiData?.status || {
    balance: 0,
    equity: 0,
    daily_pnl: 0,
    active_trades: 0,
    win_rate: 0,
    profit_factor: 0,
    total_growth: 0,
    active_symbols: ["EURUSD", "USDJPY", "AUDUSD", "USDCHF", "USDCAD", "GBPUSD", "XAUUSD"],
  };

  const symbolData = multiData?.symbols || {};
  const isRunning = botStatus.is_running;
  const activeSymbols = botStatus.active_symbols || ["EURUSD", "USDJPY", "AUDUSD", "USDCHF", "USDCAD", "GBPUSD", "XAUUSD"];
  
  const filterStatus = botStatus.filter_status || {};
  const activeCooldowns = botStatus.active_cooldowns || [];
  const activeBlockedZones = botStatus.active_blocked_zones || [];
  const strategyAnalytics = botStatus.strategy_analytics || {};
  const recentRejections = botStatus.recent_rejections || [];

  const [selectedTF, setSelectedTF] = useState("M1");
  const [selectedSession, setSelectedSession] = useState("ALL");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedTF = localStorage.getItem("selectedTF");
      const storedSession = localStorage.getItem("selectedSession");
      if (storedTF) setSelectedTF(storedTF);
      if (storedSession) setSelectedSession(storedSession);
    }
  }, []);

  const handleToggleBot = async () => {
    const endpoint = isRunning ? "stop" : "start";
    try {
      await toggleBot(endpoint).unwrap();
      toast(isRunning ? "Quant Engine Halted" : "Quant Engine Engaged", {
        icon: isRunning ? "🛑" : "🚀",
      });
    } catch (err) {
      toast.error(`Operation Failed`);
    }
  };

  const handleSaveRiskProfile = async () => {
    try {
      await updateRisk({
        risk_per_trade: parseFloat(riskParams.risk_per_trade) / 100,
        max_trades: parseInt(riskParams.max_trades),
        max_daily_trades: parseInt(riskParams.max_daily_trades),
        daily_loss_limit: parseFloat(riskParams.daily_loss) / 100,
        risk_reward_ratio: parseFloat(riskParams.risk_reward_ratio),
        preferred_session: selectedSession,
        // Partial Execution
        partial_execution_enabled: riskParams.partial_execution_enabled,
        partial_stage_1_trigger: parseFloat(riskParams.partial_stage_1_trigger) / 100,
        partial_stage_1_close_pct: parseFloat(riskParams.partial_stage_1_close_pct) / 100,
        partial_stage_2_trigger: parseFloat(riskParams.partial_stage_2_trigger) / 100,
        partial_stage_2_close_pct: parseFloat(riskParams.partial_stage_2_close_pct) / 100,
        trading_mode: riskParams.trading_mode
      }).unwrap();
      toast.success("Risk Protocol Updated");
    } catch (err) {
      toast.error("Risk Sync Failed");
    }
  };

  const updateBotSettings = async (symbols, tf, session, aiThreshold) => {
    try {
      await fetch(`${getApiBaseUrl()}/v1/settings`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          active_symbols: symbols,
          timeframe: tf,
          preferred_session: session,
          ai_confidence_threshold: aiThreshold,
        }),
      });
      if (session) {
        setSelectedSession(session);
        localStorage.setItem("selectedSession", session);
      }
      if (tf) {
        setSelectedTF(tf);
        localStorage.setItem("selectedTF", tf);
      }
      toast.success("Settings Synchronized");
    } catch (err) {
      toast.error("Update Failed");
    }
  };

  return (
    <BotContext.Provider
      value={{
        isRunning,
        botStatus,
        trades,
        history,
        customStrategies,
        depth: multiData?.depth || { bids: [], asks: [] },
        activeSymbols,
        symbolData,
        selectedTF,
        selectedSession,
        aiConfidenceThreshold: botStatus.ai_confidence_threshold || 0.48,
        filterStatus,
        activeCooldowns,
        activeBlockedZones,
        strategyAnalytics,
        recentRejections,
        riskParams,
        setRiskParams,
        isEngineSettingsOpen,
        setIsEngineSettingsOpen,
        isSidebarCollapsed,
        setIsSidebarCollapsed,
        isSidebarHidden,
        setIsSidebarHidden,
        updateBotSettings,
        toggleBot: handleToggleBot,
        saveRiskProfile: handleSaveRiskProfile,
        resetTradeHistory: () => {
          if (confirm("Permanently wipe all trade history logs?")) {
            resetHistory().unwrap().then(() => toast.success("History Purged"));
          }
        },
        deleteTradeHistoryItem: (id) => {
          if (confirm("Delete this trade from history?")) {
            deleteHistoryItem(id).unwrap().then(() => toast.success("Trade log deleted")).catch(() => toast.error("Failed to delete trade"));
          }
        },
        resetRiskProfile: () => {
          if (confirm("Restore factory risk safeguards?")) {
            resetRisk().unwrap().then(() => toast.success("Safeguards Restored"));
          }
        },
        engineConfig,
        strategySettings: { ...strategySettings, ...localStrategySettings },
        updateStrategySetting: (id, update) => {
          console.log(`📡 Transmitting Strategy Update: ${id}`, update);
          
          // Optimistic Update
          if (update.enabled !== undefined) {
             setLocalStrategySettings(prev => ({
               ...prev,
               [id]: { ...(prev[id] || (strategySettings && strategySettings[id]) || {}), enabled: update.enabled }
             }));
          }

          return updateStrategy({ strategy_id: id, ...update })
            .unwrap()
            .then((res) => {
              // Ensure we stay in sync with what the server finally confirmed
              if (res && res.settings) {
                setLocalStrategySettings(prev => ({ ...prev, [id]: res.settings }));
              }
              toast.success(`${id} Protocol Updated`, { icon: "⚙️" });
            })
            .catch((err) => {
              console.error("❌ Strategy Sync Failure:", err);
              // Rollback optimistic update
              if (strategySettings && strategySettings[id]) {
                setLocalStrategySettings(prev => ({ ...prev, [id]: strategySettings[id] }));
              }
              toast.error(`Sync Failed for ${id}`);
            });
        },
        updateSymbolManualVolume: (symbol, volume) => updateSymbolVolume({ symbol, manual_volume: volume }).unwrap().then(() => toast.success("Volume Saved")),
        addCustomStrategy: (strat) => addStrategy(strat).unwrap().then(() => toast.success("Strategy Deployed")),
        removeCustomStrategy: (id) => deleteStrategy(id).unwrap().then(() => toast.success("Strategy Purged")),
        handleCloseTrade: (ticketId) => {
          if (confirm(`Execute immediate market close for Ticket #${ticketId}?`)) {
            toast.promise(closeTrade(ticketId).unwrap(), {
              loading: 'Transmitting Close Order...',
              success: 'Trade Halted on Terminal',
              error: 'Market Exit Failed'
            });
          }
        },
      }}
    >
      {children}
    </BotContext.Provider>
  );
}

export const useBot = () => useContext(BotContext);

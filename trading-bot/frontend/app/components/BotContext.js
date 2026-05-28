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
  const { data: multiData, isLoading: isMultiLoading } = useGetMultiStatusQuery(undefined, {
    skip: !token,
  });

  const { data: trades = [], isLoading: isTradesLoading } = useGetTradesQuery(undefined, {
    skip: !token,
    pollingInterval: 5000,
  });

  const { data: history = [], isLoading: isHistoryLoading } = useGetHistoryQuery(undefined, {
    skip: !token,
    pollingInterval: 30000,
  });

  const { data: customStrategies = [] } = useGetStrategiesQuery(undefined, {
    skip: !token,
    pollingInterval: 30000,
  });

  const { data: riskData, isLoading: isRiskLoading } = useGetRiskQuery(undefined, { skip: !token });
  const { data: engineConfig = {}, isLoading: isEngineLoading } = useGetEngineConfigQuery(undefined, { skip: !token });
  const { data: strategySettings = {}, isLoading: isSettingsLoading } = useGetStrategySettingsQuery(undefined, { skip: !token });

  const isGlobalLoading = (isMultiLoading || isTradesLoading || isRiskLoading || isEngineLoading || isSettingsLoading) && token;

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
    min_setup_score: 70,
    min_ai_confidence: 0.45,
    max_spread_points: 50,
    enable_htf_filter: true,
    enable_volatility_filter: true,
    min_sl_atr_multiplier: 0.5,
    late_entry_threshold: 0.7,
    min_rr_filter: 1.0,
    enable_post_sl_cooldown: true,
    cooldown_bars_after_sl: 5,
    enable_same_zone_block: true,
    same_zone_distance_atr_multiplier: 0.25,
    enable_level_distance_filter: true,
    min_reward_to_nearest_level_rr: 1.2,
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
        min_setup_score: riskData.min_setup_score || 70,
        min_ai_confidence: riskData.min_ai_confidence || 0.45,
        max_spread_points: riskData.max_spread_points || 50,
        enable_htf_filter: riskData.enable_htf_filter ?? true,
        enable_volatility_filter: riskData.enable_volatility_filter ?? true,
        min_sl_atr_multiplier: riskData.min_sl_atr_multiplier || 0.5,
        late_entry_threshold: riskData.late_entry_threshold || 0.7,
        min_rr_filter: riskData.min_rr_filter || 1.0,
        enable_post_sl_cooldown: riskData.enable_post_sl_cooldown ?? true,
        cooldown_bars_after_sl: riskData.cooldown_bars_after_sl || 5,
        enable_same_zone_block: riskData.enable_same_zone_block ?? true,
        same_zone_distance_atr_multiplier: riskData.same_zone_distance_atr_multiplier || 0.25,
        enable_level_distance_filter: riskData.enable_level_distance_filter ?? true,
        min_reward_to_nearest_level_rr: riskData.min_reward_to_nearest_level_rr || 1.2,
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
  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedTF = localStorage.getItem("selectedTF");
      const storedSession = localStorage.getItem("selectedSession");
      if (storedTF) setSelectedTF(storedTF);
      if (storedSession) setSelectedSession(storedSession);
    }
  }, []);

  const activeSymbols = botStatus.active_symbols || ["EURUSD", "USDJPY", "AUDUSD", "USDCHF", "USDCAD", "GBPUSD", "XAUUSD"];
  const filterStatus = botStatus.filter_status || {};
  const activeCooldowns = botStatus.active_cooldowns || [];
  const activeBlockedZones = botStatus.active_blocked_zones || [];
  const strategyAnalytics = botStatus.strategy_analytics || {};
  const recentRejections = botStatus.recent_rejections || [];

  const [selectedTF, setSelectedTF] = useState("M1");
  const [selectedSession, setSelectedSession] = useState("ALL");
  const [optimisticIsRunning, setOptimisticIsRunning] = useState(null);

  useEffect(() => {
    // Sync optimistic state back to null once server data catches up
    if (optimisticIsRunning !== null && botStatus.is_running === optimisticIsRunning) {
      setOptimisticIsRunning(null);
    }
  }, [botStatus.is_running]);

  const handleToggleBot = async () => {
    const nextState = !isRunning;
    setOptimisticIsRunning(nextState);
    const endpoint = nextState ? "start" : "stop";
    
    try {
      await toggleBot(endpoint).unwrap();
      toast(nextState ? "Quant Engine Engaged" : "Quant Engine Halted", {
        icon: nextState ? "🚀" : "🛑",
      });
    } catch (err) {
      setOptimisticIsRunning(null); // Rollback on failure
      toast.error(`Operation Failed`);
    }
  };

  const isRunning = optimisticIsRunning !== null ? optimisticIsRunning : (botStatus.is_running || false);

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
        min_setup_score: parseFloat(riskParams.min_setup_score),
        min_ai_confidence: parseFloat(riskParams.min_ai_confidence),
        max_spread_points: parseFloat(riskParams.max_spread_points),
        enable_htf_filter: riskParams.enable_htf_filter,
        enable_volatility_filter: riskParams.enable_volatility_filter,
        min_sl_atr_multiplier: parseFloat(riskParams.min_sl_atr_multiplier),
        late_entry_threshold: parseFloat(riskParams.late_entry_threshold),
        min_rr_filter: parseFloat(riskParams.min_rr_filter),
        enable_post_sl_cooldown: riskParams.enable_post_sl_cooldown,
        cooldown_bars_after_sl: parseInt(riskParams.cooldown_bars_after_sl),
        enable_same_zone_block: riskParams.enable_same_zone_block,
        same_zone_distance_atr_multiplier: parseFloat(riskParams.same_zone_distance_atr_multiplier),
        enable_level_distance_filter: riskParams.enable_level_distance_filter,
        min_reward_to_nearest_level_rr: parseFloat(riskParams.min_reward_to_nearest_level_rr),
        trading_mode: riskParams.trading_mode
      }).unwrap();
      toast.success("Risk Protocol Updated");
    } catch (err) {
      toast.error("Risk Sync Failed");
    }
  };

  const updateBotSettings = async (symbols, tf, session, aiThreshold) => {
    try {
      await fetch(`${getApiBaseUrl()}/v1/legacy/settings`, {
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
        isGlobalLoading,
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

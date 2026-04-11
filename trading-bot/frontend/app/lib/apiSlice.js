import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { getApiBaseUrl, getWsBaseUrl } from './config';

const baseQuery = fetchBaseQuery({
  baseUrl: `${getApiBaseUrl()}/v1`,
  prepareHeaders: (headers) => {
    const token = localStorage.getItem('quant_token');
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  },
});

const baseQueryWithReauth = async (args, api, extraOptions) => {
  let result = await baseQuery(args, api, extraOptions);
  
  if (result.error && result.error.status === 401) {
    const refreshToken = localStorage.getItem('quant_refresh');
    
    if (refreshToken) {
      try {
        const refreshResult = await fetch(`${getApiBaseUrl()}/v1/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken })
        });
        
        if (refreshResult.ok) {
          const data = await refreshResult.json();
          localStorage.setItem('quant_token', data.access_token);
          localStorage.setItem('quant_refresh', data.refresh_token);
          
          // Retry the original query with new token
          result = await baseQuery(args, api, extraOptions);
          return result;
        }
      } catch (e) {
        console.error("Token refresh failed");
      }
    }
    
    // Refresh failed or no refresh token
    localStorage.removeItem('quant_token');
    localStorage.removeItem('quant_refresh');
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
  }
  return result;
};

export const tradingApi = createApi({
  reducerPath: 'tradingApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Status', 'Trades', 'History', 'Strategy', 'EngineConfig'],
  endpoints: (builder) => ({
    getMultiStatus: builder.query({
      query: () => '/legacy/multi-status',
      providesTags: ['Status'],
      keepUnusedDataFor: 60,
      async onCacheEntryAdded(arg, { updateCachedData, cacheDataLoaded, cacheEntryRemoved }) {
        const ws = new WebSocket(`${getWsBaseUrl()}/ws/status`);
        try {
          await cacheDataLoaded;
          ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            updateCachedData((draft) => {
              if (data.status) draft.status = data.status;
              if (data.symbols) draft.symbols = data.symbols;
              if (data.depth) draft.depth = data.depth;
            });
          };
        } catch {}
        await cacheEntryRemoved;
        ws.close();
      },
    }),
    getTrades: builder.query({
      query: () => '/trades',
      providesTags: ['Trades'],
    }),
    getHistory: builder.query({
      query: () => '/legacy/history',
      providesTags: ['History'],
    }),
    getRisk: builder.query({
      query: () => '/risk',
    }),
    getEngineConfig: builder.query({
      query: () => '/legacy/symbols/engine-config',
      providesTags: ['EngineConfig'],
    }),
    getStrategySettings: builder.query({
      query: () => '/legacy/settings/strategy',
      providesTags: ['Strategy'],
    }),
    getStrategies: builder.query({
      query: () => '/legacy/strategies',
      providesTags: ['Strategy'],
    }),
    searchSymbols: builder.query({
      query: (q) => `/legacy/symbols/search?q=${q}`,
    }),
    
    toggleBot: builder.mutation({
      query: (endpoint) => ({
        url: `/bot/${endpoint}`,
        method: 'POST',
      }),
      invalidatesTags: ['Status'],
    }),
    updateRisk: builder.mutation({
      query: (settings) => ({
        url: '/risk',
        method: 'POST',
        body: settings,
      }),
    }),
    updateStrategy: builder.mutation({
      query: (update) => ({
        url: '/legacy/settings/strategy',
        method: 'POST',
        body: update,
      }),
      invalidatesTags: ['Strategy'],
    }),
    addStrategy: builder.mutation({
      query: (newStrategy) => ({
        url: '/legacy/strategies',
        method: 'POST',
        body: newStrategy,
      }),
      invalidatesTags: ['Strategy'],
    }),
    deleteStrategy: builder.mutation({
      query: (id) => ({
        url: `/legacy/strategies/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Strategy'],
    }),
    updateSymbolVolume: builder.mutation({
      query: (update) => ({
        url: '/legacy/settings/symbol',
        method: 'POST',
        body: update,
      }),
      invalidatesTags: ['EngineConfig'],
    }),
    resetHistory: builder.mutation({
      query: () => ({
        url: '/legacy/reset/history',
        method: 'POST',
      }),
      invalidatesTags: ['History', 'Trades'],
    }),
    deleteHistoryItem: builder.mutation({
      query: (ticketId) => ({
        url: `/legacy/history/${ticketId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['History'],
    }),
    resetRisk: builder.mutation({
      query: () => ({
        url: '/legacy/reset/risk',
        method: 'POST',
      }),
      invalidatesTags: ['Status'],
    }),
    closeTrade: builder.mutation({
      query: (ticketId) => ({
        url: `/trades/${ticketId}/close`,
        method: 'POST',
      }),
      invalidatesTags: ['Trades', 'Status'],
    }),
  }),
});

export const {
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
  useSearchSymbolsQuery,
  useDeleteHistoryItemMutation,
  useCloseTradeMutation,
} = tradingApi;

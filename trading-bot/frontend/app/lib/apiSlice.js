import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { getApiBaseUrl, getWsBaseUrl } from './config';

export const tradingApi = createApi({
  reducerPath: 'tradingApi',
  baseQuery: fetchBaseQuery({
    baseUrl: getApiBaseUrl(),
    prepareHeaders: (headers) => {
      const token = localStorage.getItem('token');
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Status', 'Trades', 'History', 'Strategy', 'EngineConfig'],
  endpoints: (builder) => ({
    getMultiStatus: builder.query({
      query: () => '/multi-status',
      providesTags: ['Status'],
      // Keep data for 1 minute in cache, but poll every 3s
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
      query: () => '/history',
      providesTags: ['History'],
    }),
    getRisk: builder.query({
      query: () => '/risk',
    }),
    getEngineConfig: builder.query({
      query: () => '/symbols/engine-config',
      providesTags: ['EngineConfig'],
    }),
    getStrategySettings: builder.query({
      query: () => '/settings/strategy',
      providesTags: ['Strategy'],
    }),
    getStrategies: builder.query({
      query: () => '/strategies',
      providesTags: ['Strategy'],
    }),
    searchSymbols: builder.query({
      query: (q) => `/symbols/search?q=${q}`,
    }),
    
    // Mutations for updates
    toggleBot: builder.mutation({
      query: (endpoint) => ({
        url: `/${endpoint}`,
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
        url: '/settings/strategy',
        method: 'POST',
        body: update,
      }),
      invalidatesTags: ['Strategy'],
    }),
    addStrategy: builder.mutation({
      query: (newStrategy) => ({
        url: '/strategies',
        method: 'POST',
        body: newStrategy,
      }),
      invalidatesTags: ['Strategy'],
    }),
    deleteStrategy: builder.mutation({
      query: (id) => ({
        url: `/strategies/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Strategy'],
    }),
    updateSymbolVolume: builder.mutation({
      query: (update) => ({
        url: '/settings/symbol',
        method: 'POST',
        body: update,
      }),
      invalidatesTags: ['EngineConfig'],
    }),
    resetHistory: builder.mutation({
      query: () => ({
        url: '/reset/history',
        method: 'POST',
      }),
      invalidatesTags: ['History', 'Trades'],
    }),
    deleteHistoryItem: builder.mutation({
      query: (ticketId) => ({
        url: `/history/${ticketId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['History'],
    }),
    resetRisk: builder.mutation({
      query: () => ({
        url: '/reset/risk',
        method: 'POST',
      }),
      invalidatesTags: ['Status'],
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
} = tradingApi;

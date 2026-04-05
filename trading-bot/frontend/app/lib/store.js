import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { tradingApi } from './apiSlice';

export const makeStore = () => {
  return configureStore({
    reducer: {
      [tradingApi.reducerPath]: tradingApi.reducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(tradingApi.middleware),
  });
};

// optional, but required for refetchOnFocus/refetchOnReconnect behaviors
// setupListeners(store.dispatch)

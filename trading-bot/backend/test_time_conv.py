import pandas as pd
import numpy as np

# Simulate MT5 rates
data = {
    'time': [1741725797, 1741725857],
    'open': [1.1, 1.11],
    'high': [1.2, 1.21],
    'low': [1.0, 1.01],
    'close': [1.15, 1.16]
}
df = pd.DataFrame(data)

# Simulate MT5Client.get_bars
df['time'] = pd.to_datetime(df['time'], unit='s')
print(f"Type after to_datetime: {df['time'].dtype}")

# Simulate BotWorker._process_symbol
df_export = df.copy()
df_export['time_int'] = df_export['time'].astype('int64')
df_export['time_final'] = df_export['time_int'] // 10**9

# Test robust conversion
df_export['time_robust'] = df_export['time'].values.astype('datetime64[s]').astype('int64')
print(f"Robust result: {df_export['time_robust'].iloc[0]}")

# Test with ns resolution
df['time_ns'] = pd.to_datetime(data['time'], unit='s').astype('datetime64[ns]')
print(f"Type of time_ns: {df['time_ns'].dtype}")
df_export['time_ns_robust'] = df['time_ns'].values.astype('datetime64[s]').astype('int64')
print(f"Robust result for ns: {df_export['time_ns_robust'].iloc[0]}")

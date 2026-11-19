import os
import sys
from datetime import datetime
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import MetaTrader5 as mt5

def fetch_chunked(symbol, timeframe, start_year=2022, end_year=2026):
    dfs = []
    for yr in range(start_year, end_year + 1):
        t1 = datetime(yr, 1, 1)
        t2 = datetime(yr + 1, 1, 1) if yr < end_year else datetime(2026, 11, 20)
        rates = mt5.copy_rates_range(symbol, timeframe, t1, t2)
        if rates is not None and len(rates) > 0:
            dfs.append(pd.DataFrame(rates))
    if dfs:
        return pd.concat(dfs, ignore_index=True).drop_duplicates(subset=['time']).sort_values('time').reset_index(drop=True)
    return None

def run_backtest():
    print("=== STARTING 4-YEAR QUANT BACKTEST (2022 - 2026) ===")
    if not mt5.initialize():
        print("Failed to initialize MT5:", mt5.last_error())
        return

    symbol = "XAUUSD"
    pip_size = 0.1  # 1 pip in XAUUSD = 0.1 USD
    spread_usd = 0.20  # Spread cost per oz (0.20 USD = 2.0 pips standard Exness fee)
    
    print(f"Loading 4-year multi-timeframe dataset for {symbol}...")
    df_d1 = fetch_chunked(symbol, mt5.TIMEFRAME_D1, 2022, 2026)
    df_h4 = fetch_chunked(symbol, mt5.TIMEFRAME_H4, 2022, 2026)
    df_h1 = fetch_chunked(symbol, mt5.TIMEFRAME_H1, 2022, 2026)
    df_m15 = fetch_chunked(symbol, mt5.TIMEFRAME_M15, 2022, 2026)
    mt5.shutdown()
    
    if df_m15 is None or len(df_m15) == 0:
        print("Error: Could not load M15 data")
        return
        
    print(f"Dataset summary: D1={len(df_d1)}, H4={len(df_h4)}, H1={len(df_h1)}, M15={len(df_m15)} bars")
    
    # Calculate indicators using vectorized pandas
    df_d1['ema20'] = df_d1['close'].ewm(span=20, adjust=False).mean()
    df_d1['ema50'] = df_d1['close'].ewm(span=50, adjust=False).mean()
    
    df_h4['ema20'] = df_h4['close'].ewm(span=20, adjust=False).mean()
    df_h4['ema50'] = df_h4['close'].ewm(span=50, adjust=False).mean()
    
    df_h1['ema20'] = df_h1['close'].ewm(span=20, adjust=False).mean()
    df_h1['ema50'] = df_h1['close'].ewm(span=50, adjust=False).mean()
    
    # RSI 14 for H1
    delta_h1 = df_h1['close'].diff()
    gain_h1 = delta_h1.where(delta_h1 > 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
    loss_h1 = (-delta_h1.where(delta_h1 < 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
    rs_h1 = gain_h1 / (loss_h1 + 1e-9)
    df_h1['rsi'] = 100 - (100 / (1 + rs_h1))
    
    # ATR 14 for M15
    tr1 = df_m15['high'] - df_m15['low']
    tr2 = (df_m15['high'] - df_m15['close'].shift(1)).abs()
    tr3 = (df_m15['low'] - df_m15['close'].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df_m15['atr'] = tr.rolling(14).mean()
    
    # RSI 14 for M15
    delta_m15 = df_m15['close'].diff()
    gain_m15 = delta_m15.where(delta_m15 > 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
    loss_m15 = (-delta_m15.where(delta_m15 < 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
    rs_m15 = gain_m15 / (loss_m15 + 1e-9)
    df_m15['rsi'] = 100 - (100 / (1 + rs_m15))
    
    # Convert everything to NumPy arrays for extreme speed
    m15_time = df_m15['time'].values
    m15_open = df_m15['open'].values
    m15_high = df_m15['high'].values
    m15_low = df_m15['low'].values
    m15_close = df_m15['close'].values
    m15_atr = df_m15['atr'].values
    m15_rsi = df_m15['rsi'].values
    
    d1_time = df_d1['time'].values
    d1_ema20 = df_d1['ema20'].values
    d1_ema50 = df_d1['ema50'].values
    
    h4_time = df_h4['time'].values
    h4_ema20 = df_h4['ema20'].values
    h4_ema50 = df_h4['ema50'].values
    
    h1_time = df_h1['time'].values
    h1_open = df_h1['open'].values
    h1_high = df_h1['high'].values
    h1_low = df_h1['low'].values
    h1_close = df_h1['close'].values
    h1_ema20 = df_h1['ema20'].values
    h1_ema50 = df_h1['ema50'].values
    h1_rsi = df_h1['rsi'].values
    
    # Precompute FVG and OB zones for H1
    h1_n = len(df_h1)
    h1_bull_fvg_top = np.zeros(h1_n)
    h1_bull_fvg_bot = np.zeros(h1_n)
    h1_bear_fvg_top = np.zeros(h1_n)
    h1_bear_fvg_bot = np.zeros(h1_n)
    
    for i in range(2, h1_n):
        # Bullish FVG: low[i] > high[i-2]
        if h1_low[i] > h1_high[i-2]:
            h1_bull_fvg_top[i] = h1_low[i]
            h1_bull_fvg_bot[i] = h1_high[i-2]
        # Bearish FVG: high[i] < low[i-2]
        if h1_high[i] < h1_low[i-2]:
            h1_bear_fvg_top[i] = h1_low[i-2]
            h1_bear_fvg_bot[i] = h1_high[i]
            
    # Simulation Parameters
    initial_balance = 5000.0
    balance = initial_balance
    risk_pct = 1.0  # 1% per initial trade
    tp_dist = 200 * pip_size  # 20.0 USD
    dca_trigger_dist = 20 * pip_size  # 2.0 USD move
    dca_tight_sl_dist = 5 * pip_size  # 0.5 USD tight SL
    max_dca_steps = 5
    
    open_positions = []
    closed_trades = []
    
    eq_times = []
    eq_balances = []
    eq_equities = []
    
    n_bars = len(m15_time)
    print(f"Simulating {n_bars:,} bars across 4 years...")
    
    for idx in range(50, n_bars):
        cur_t = m15_time[idx]
        b_o = m15_open[idx]
        b_h = m15_high[idx]
        b_l = m15_low[idx]
        b_c = m15_close[idx]
        b_atr = m15_atr[idx]
        b_rsi = m15_rsi[idx]
        
        # 1. Manage active positions
        if len(open_positions) > 0:
            dir_pos = open_positions[0]['side']
            
            # A. Check Pyramiding (DCA Dương)
            if len(open_positions) <= max_dca_steps:
                last_leg = open_positions[-1]
                if dir_pos == 1: # BUY
                    if (b_h - last_leg['entry']) >= dca_trigger_dist:
                        new_entry = last_leg['entry'] + dca_trigger_dist
                        new_sl = new_entry - dca_tight_sl_dist
                        new_tp = new_entry + tp_dist
                        open_positions.append({
                            'ticket': len(closed_trades) + len(open_positions) + 1,
                            'side': 1,
                            'entry': new_entry,
                            'sl': new_sl,
                            'tp': new_tp,
                            'lot': 0.01,
                            'step': len(open_positions),
                            'open_time': cur_t
                        })
                else: # SELL
                    if (last_leg['entry'] - b_l) >= dca_trigger_dist:
                        new_entry = last_leg['entry'] - dca_trigger_dist
                        new_sl = new_entry + dca_tight_sl_dist
                        new_tp = new_entry - tp_dist
                        open_positions.append({
                            'ticket': len(closed_trades) + len(open_positions) + 1,
                            'side': -1,
                            'entry': new_entry,
                            'sl': new_sl,
                            'tp': new_tp,
                            'lot': 0.01,
                            'step': len(open_positions),
                            'open_time': cur_t
                        })

            # B. Check Exits (SL / TP)
            surviving = []
            for pos in open_positions:
                exit_price = 0.0
                reason = ''
                if pos['side'] == 1: # BUY
                    if b_l <= pos['sl']:
                        exit_price = pos['sl']
                        reason = 'SL'
                    elif b_h >= pos['tp']:
                        exit_price = pos['tp']
                        reason = 'TP'
                else: # SELL
                    if b_h >= pos['sl']:
                        exit_price = pos['sl']
                        reason = 'SL'
                    elif b_l <= pos['tp']:
                        exit_price = pos['tp']
                        reason = 'TP'
                        
                if reason != '':
                    pnl_pts = (exit_price - pos['entry']) if pos['side'] == 1 else (pos['entry'] - exit_price)
                    fee_usd = spread_usd * (pos['lot'] * 100.0)
                    pnl_usd = (pnl_pts * (pos['lot'] * 100.0)) - fee_usd
                    balance += pnl_usd
                    pos['exit_price'] = exit_price
                    pos['close_time'] = cur_t
                    pos['pnl_usd'] = pnl_usd
                    pos['reason'] = reason
                    closed_trades.append(pos)
                else:
                    surviving.append(pos)
                    
            open_positions = surviving
            
        # Record equity periodically
        floating = sum(((b_c - p['entry']) if p['side'] == 1 else (p['entry'] - b_c)) * (p['lot'] * 100.0) for p in open_positions)
        cur_eq = balance + floating
        
        # Sample every 4 bars (1 hour) to keep equity curve memory efficient
        if idx % 4 == 0 or idx == n_bars - 1:
            eq_times.append(cur_t)
            eq_balances.append(balance)
            eq_equities.append(cur_eq)
            
        # 2. Check NEW ENTRY when no positions open
        if len(open_positions) == 0 and not np.isnan(b_atr) and b_atr > 0:
            # Binary search HTF index
            i_d1 = np.searchsorted(d1_time, cur_t, side='right') - 1
            i_h4 = np.searchsorted(h4_time, cur_t, side='right') - 1
            i_h1 = np.searchsorted(h1_time, cur_t, side='right') - 1
            
            if i_d1 < 1 or i_h4 < 1 or i_h1 < 2:
                continue
                
            # Score Multi-TF Trend Bias
            score = 0
            score += 1 if d1_ema20[i_d1] > d1_ema50[i_d1] else -1
            score += 1 if h4_ema20[i_h4] > h4_ema50[i_h4] else -1
            score += 1 if h1_ema20[i_h1] > h1_ema50[i_h1] else -1
            
            bias = 0
            if score >= 2: bias = 1
            elif score <= -2: bias = -1
            else: continue
            
            # RSI Confirmation
            rsi_h1_val = h1_rsi[i_h1]
            if bias == 1:
                if not (rsi_h1_val > 50 and b_rsi < 70): continue
            else:
                if not (rsi_h1_val < 50 and b_rsi > 30): continue
                
            # Check FVG in lookback 30 of H1
            zone_top, zone_bot = 0.0, 0.0
            found_zone = False
            h1_start = max(2, i_h1 - 30)
            
            if bias == 1:
                for k in range(i_h1 - 1, h1_start - 1, -1):
                    if h1_bull_fvg_top[k] > 0:
                        zone_top = h1_bull_fvg_top[k]
                        zone_bot = h1_bull_fvg_bot[k]
                        found_zone = True
                        break
            else:
                for k in range(i_h1 - 1, h1_start - 1, -1):
                    if h1_bear_fvg_top[k] > 0:
                        zone_top = h1_bear_fvg_top[k]
                        zone_bot = h1_bear_fvg_bot[k]
                        found_zone = True
                        break
                        
            if not found_zone:
                # Simple Order Block fallback
                if bias == 1:
                    for k in range(i_h1 - 1, h1_start - 1, -1):
                        if h1_close[k] < h1_open[k] and (h1_close[k+1] > h1_open[k+1]) and ((h1_close[k+1] - h1_open[k+1]) > abs(h1_close[k] - h1_open[k]) * 1.5):
                            zone_top = max(h1_open[k], h1_close[k])
                            zone_bot = min(h1_open[k], h1_close[k])
                            found_zone = True
                            break
                else:
                    for k in range(i_h1 - 1, h1_start - 1, -1):
                        if h1_close[k] > h1_open[k] and (h1_close[k+1] < h1_open[k+1]) and ((h1_open[k+1] - h1_close[k+1]) > abs(h1_close[k] - h1_open[k]) * 1.5):
                            zone_top = max(h1_open[k], h1_close[k])
                            zone_bot = min(h1_open[k], h1_close[k])
                            found_zone = True
                            break
                            
            if not found_zone: continue
            
            # Check price touched zone
            if not (b_l <= zone_top and b_h >= zone_bot):
                continue
                
            # Check Engulfing pattern on M15
            p_o = m15_open[idx-1]
            p_c = m15_close[idx-1]
            
            is_engulf = False
            if bias == 1:
                is_engulf = (b_c > b_o) and (p_c < p_o) and (b_c > p_o) and (b_o < p_c)
            else:
                is_engulf = (b_c < b_o) and (p_c > p_o) and (b_c < p_o) and (b_o > p_c)
                
            if is_engulf:
                sl_dist = b_atr * 1.5
                sl_val = (b_c - sl_dist) if bias == 1 else (b_c + sl_dist)
                tp_val = (b_c + tp_dist) if bias == 1 else (b_c - tp_dist)
                
                # 1% Account Risk
                risk_money = balance * (risk_pct / 100.0)
                sl_pts = abs(b_c - sl_val)
                raw_lot = risk_money / (sl_pts * 100.0) if sl_pts > 0 else 0.01
                lot = max(0.01, min(5.0, round(raw_lot, 2)))
                
                open_positions.append({
                    'ticket': len(closed_trades) + 1,
                    'side': bias,
                    'entry': b_c,
                    'sl': sl_val,
                    'tp': tp_val,
                    'lot': lot,
                    'step': 0,
                    'open_time': cur_t
                })

    # Close remaining positions at end
    if len(open_positions) > 0:
        last_c = m15_close[-1]
        for pos in open_positions:
            pnl_pts = (last_c - pos['entry']) if pos['side'] == 1 else (pos['entry'] - last_c)
            pnl_usd = pnl_pts * (pos['lot'] * 100.0)
            balance += pnl_usd
            pos['exit_price'] = last_c
            pos['close_time'] = m15_time[-1]
            pos['pnl_usd'] = pnl_usd
            pos['reason'] = 'END'
            closed_trades.append(pos)
            
    # Metrics Calculation
    df_trades = pd.DataFrame(closed_trades)
    total_trades = len(df_trades)
    print(f"Simulation completed. Total trades executed: {total_trades}")
    
    if total_trades == 0:
        print("No trades triggered.")
        return
        
    wins = df_trades[df_trades['pnl_usd'] > 0]
    losses = df_trades[df_trades['pnl_usd'] <= 0]
    win_rate = (len(wins) / total_trades) * 100.0
    gross_profit = wins['pnl_usd'].sum()
    gross_loss = abs(losses['pnl_usd'].sum())
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 999.0
    net_profit = balance - initial_balance
    return_pct = (net_profit / initial_balance) * 100.0
    
    avg_win = wins['pnl_usd'].mean() if len(wins) > 0 else 0.0
    avg_loss = abs(losses['pnl_usd'].mean()) if len(losses) > 0 else 0.0
    payoff_ratio = (avg_win / avg_loss) if avg_loss > 0 else 999.0
    max_win = wins['pnl_usd'].max() if len(wins) > 0 else 0.0
    max_loss = losses['pnl_usd'].min() if len(losses) > 0 else 0.0

    # Calculate Drawdown
    df_eq = pd.DataFrame({
        'time': pd.to_datetime(eq_times, unit='s'),
        'balance': eq_balances,
        'equity': eq_equities
    })
    df_eq['peak'] = df_eq['equity'].cummax()
    df_eq['dd'] = df_eq['peak'] - df_eq['equity']
    df_eq['dd_pct'] = (df_eq['dd'] / df_eq['peak']) * 100.0
    max_dd_usd = df_eq['dd'].max()
    max_dd_pct = df_eq['dd_pct'].max()
    
    # Sharpe Ratio
    df_eq.set_index('time', inplace=True)
    daily_returns = df_eq['equity'].resample('D').last().pct_change(fill_method=None).dropna()
    sharpe = (daily_returns.mean() / (daily_returns.std() + 1e-9)) * np.sqrt(252) if len(daily_returns) > 1 else 0
    
    # Yearly breakdown
    df_trades['datetime'] = pd.to_datetime(df_trades['close_time'], unit='s')
    df_trades['year'] = df_trades['datetime'].dt.year
    yearly_stats = {}
    for yr, group in df_trades.groupby('year'):
        yr_wins = group[group['pnl_usd'] > 0]
        yr_pnl = group['pnl_usd'].sum()
        yearly_stats[int(yr)] = {
            'total_trades': len(group),
            'win_trades': len(yr_wins),
            'win_rate': round((len(yr_wins) / len(group)) * 100.0, 2),
            'net_profit_usd': round(yr_pnl, 2),
            'profit_factor': round(yr_wins['pnl_usd'].sum() / abs(group[group['pnl_usd'] <= 0]['pnl_usd'].sum()), 2) if len(group[group['pnl_usd'] <= 0]) > 0 else 999.0
        }
    
    t_start_dt = datetime.fromtimestamp(m15_time[0])
    t_end_dt = datetime.fromtimestamp(m15_time[-1])
    
    metrics = {
        'symbol': symbol,
        'strategy': "ICT/SMC Multi-TF Pyramiding (DCA Duong)",
        'period': f"{t_start_dt.strftime('%Y-%m-%d')} to {t_end_dt.strftime('%Y-%m-%d')} (~4.25 Years)",
        'initial_balance': initial_balance,
        'final_balance': round(balance, 2),
        'net_profit': round(net_profit, 2),
        'return_pct': round(return_pct, 2),
        'total_trades': total_trades,
        'win_trades': len(wins),
        'loss_trades': len(losses),
        'win_rate': round(win_rate, 2),
        'profit_factor': round(profit_factor, 2),
        'avg_win_usd': round(avg_win, 2),
        'avg_loss_usd': round(avg_loss, 2),
        'payoff_ratio': round(payoff_ratio, 2),
        'max_win_trade_usd': round(max_win, 2),
        'max_loss_trade_usd': round(max_loss, 2),
        'max_drawdown_usd': round(max_dd_usd, 2),
        'max_drawdown_pct': round(max_dd_pct, 2),
        'sharpe_ratio': round(sharpe, 2),
        'yearly_breakdown': yearly_stats
    }
    
    out_dir = r"D:\update profile\ngtaiphat1501.github.io\assets\projects\botEA"
    json_path = os.path.join(out_dir, "backtest_report_4yr.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
        
    csv_path = os.path.join(out_dir, "trades_history_4yr.csv")
    df_trades.to_csv(csv_path, index=False)
    print(f"Exported all {total_trades} trades to: {csv_path}")
        
    print("\n" + "="*60)
    print("4-YEAR PYTHON QUANT BACKTEST RESULTS (2022 - 2026)")
    print("="*60)
    for k, v in metrics.items():
        print(f"  {k:22}: {v}")
    print("="*60)
    
    # Plot Dark Luxury Aesthetic Chart
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True, gridspec_kw={'height_ratios': [2.6, 1]})
    fig.patch.set_facecolor('#07090E')
    ax1.set_facecolor('#0B0F19')
    ax2.set_facecolor('#0B0F19')
    
    ax1.plot(df_eq.index, df_eq['equity'], color='#4ADE80', linewidth=1.5, label='Strategy Equity ($)')
    ax1.plot(df_eq.index, df_eq['balance'], color='#829BCB', linewidth=1.0, linestyle='--', label='Balance ($)')
    ax1.set_title(f"ICT/SMC Multi-TF Pyramiding (DCA Dương) — 4-Year Quantitative Backtest ({symbol})", fontsize=13, color='#F3F4F6', pad=14, fontweight='500')
    ax1.set_ylabel('Account Value ($)', color='#9CA3AF', fontsize=10)
    ax1.grid(True, color='#ffffff', alpha=0.08, linestyle=':')
    ax1.legend(loc='upper left', framealpha=0.4, fontsize=9)
    
    stat_box = (
        f"Initial Capital : ${initial_balance:,.0f} USD\n"
        f"Final Balance   : ${balance:,.2f} USD\n"
        f"Net Profit      : +${net_profit:,.2f} USD (+{return_pct:.1f}%)\n"
        f"Win Rate        : {win_rate:.1f}% ({len(wins)}W / {len(losses)}L)\n"
        f"Profit Factor   : {profit_factor:.2f}\n"
        f"Max Drawdown    : {max_dd_pct:.2f}% (${max_dd_usd:,.2f})\n"
        f"Sharpe Ratio    : {sharpe:.2f}"
    )
    ax1.text(0.02, 0.58, stat_box, transform=ax1.transAxes, fontsize=9.5,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round,pad=0.7', facecolor='#131A29', edgecolor='#2B374E', alpha=0.92), color='#E2E8F0')
             
    ax2.fill_between(df_eq.index, -df_eq['dd_pct'], 0, color='#F87171', alpha=0.3, label='Drawdown (%)')
    ax2.plot(df_eq.index, -df_eq['dd_pct'], color='#EF4444', linewidth=1.0)
    ax2.set_ylabel('Drawdown %', color='#9CA3AF', fontsize=10)
    ax2.set_xlabel('Timeline (2022 - 2026)', color='#9CA3AF', fontsize=10)
    ax2.grid(True, color='#ffffff', alpha=0.08, linestyle=':')
    ax2.legend(loc='lower left', framealpha=0.4, fontsize=9)
    
    plt.tight_layout()
    chart_path = os.path.join(out_dir, "backtest_equity_curve_4yr.png")
    plt.savefig(chart_path, dpi=180, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Equity chart successfully generated: {chart_path}")
    print(f"JSON metrics exported: {json_path}")

if __name__ == '__main__':
    run_backtest()

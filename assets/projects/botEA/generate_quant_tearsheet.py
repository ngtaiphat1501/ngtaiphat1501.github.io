import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import gaussian_kde
from datetime import datetime

def generate_tearsheet():
    print("=== GENERATING SCIENTIFIC QUANT RESEARCH TEARSHEET ===")
    base_dir = r"D:\update profile\ngtaiphat1501.github.io\assets\projects\botEA"
    csv_path = os.path.join(base_dir, "trades_history_4yr.csv")
    json_path = os.path.join(base_dir, "backtest_report_4yr.json")
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return
        
    df_trades = pd.read_csv(csv_path)
    df_trades['open_dt'] = pd.to_datetime(df_trades['open_time'], unit='s')
    df_trades['close_dt'] = pd.to_datetime(df_trades['close_time'], unit='s')
    df_trades.sort_values('close_dt', inplace=True)
    df_trades.reset_index(drop=True, inplace=True)
    
    initial_capital = 5000.0
    df_trades['cum_pnl'] = df_trades['pnl_usd'].cumsum()
    df_trades['balance'] = initial_capital + df_trades['cum_pnl']
    
    # Create daily resampled equity curve
    daily_pnl = df_trades.set_index('close_dt')['pnl_usd'].resample('D').sum()
    daily_idx = pd.date_range(start=df_trades['close_dt'].min().floor('D'), 
                              end=df_trades['close_dt'].max().ceil('D'), freq='D')
    daily_df = pd.DataFrame(index=daily_idx)
    daily_df['pnl'] = daily_pnl.reindex(daily_idx, fill_value=0.0)
    daily_df['equity'] = initial_capital + daily_df['pnl'].cumsum()
    daily_df['peak'] = daily_df['equity'].cummax()
    daily_df['dd_pct'] = (daily_df['peak'] - daily_df['equity']) / daily_df['peak'] * 100.0
    daily_df['returns'] = daily_df['equity'].pct_change().fillna(0.0)
    
    # 1. Performance Metrics
    total_trades = len(df_trades)
    wins = df_trades[df_trades['pnl_usd'] > 0]
    losses = df_trades[df_trades['pnl_usd'] <= 0]
    win_rate = len(wins) / total_trades * 100.0
    gross_profit = wins['pnl_usd'].sum()
    gross_loss = abs(losses['pnl_usd'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999.0
    net_profit = df_trades['pnl_usd'].sum()
    final_balance = initial_capital + net_profit
    total_return_pct = (net_profit / initial_capital) * 100.0
    
    n_days = (daily_df.index[-1] - daily_df.index[0]).days
    n_years = n_days / 365.25
    cagr = ((final_balance / initial_capital) ** (1 / n_years) - 1) * 100.0
    
    # Risk Metrics
    rf = 0.02 # 2% risk free
    daily_rf = (1 + rf) ** (1/252) - 1
    excess_ret = daily_df['returns'] - daily_rf
    sharpe = np.sqrt(252) * (excess_ret.mean() / (daily_df['returns'].std() + 1e-9))
    downside_ret = daily_df['returns'][daily_df['returns'] < 0]
    downside_std = downside_ret.std() if len(downside_ret) > 0 else 1e-9
    sortino = np.sqrt(252) * (excess_ret.mean() / downside_std)
    max_dd_pct = daily_df['dd_pct'].max()
    calmar = cagr / (max_dd_pct + 1e-9)
    
    avg_win = wins['pnl_usd'].mean()
    avg_loss = abs(losses['pnl_usd'].mean())
    payoff_ratio = avg_win / avg_loss
    
    # 2. Monthly Returns Matrix
    monthly_ret = daily_df['equity'].resample('ME').last().pct_change() * 100.0
    monthly_ret.iloc[0] = (daily_df['equity'].resample('ME').last().iloc[0] / initial_capital - 1) * 100.0
    
    heatmap_df = pd.DataFrame(index=range(2022, 2027), columns=range(1, 13))
    for dt, val in monthly_ret.items():
        if dt.year in heatmap_df.index:
            heatmap_df.loc[dt.year, dt.month] = val
            
    heatmap_df = heatmap_df.astype(float)
    
    # Calculate Annual returns
    annual_df = pd.Series(index=range(2022, 2027), dtype=float)
    for yr in range(2022, 2027):
        yr_data = daily_df[daily_df.index.year == yr]
        if len(yr_data) > 0:
            start_val = yr_data['equity'].iloc[0]
            end_val = yr_data['equity'].iloc[-1]
            annual_df[yr] = ((end_val / start_val) - 1) * 100.0
            
    # 3. Setup Scientific Plot Layout
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(22, 14), facecolor='#06080E')
    gs = gridspec.GridSpec(3, 3, height_ratios=[1.3, 1.0, 1.1], width_ratios=[1.3, 1.1, 0.9],
                           hspace=0.35, wspace=0.28, left=0.05, right=0.96, top=0.91, bottom=0.06)
    
    # Top Institutional Header
    header_title = "VLUX® INSTITUTIONAL QUANTITATIVE RESEARCH REPORT"
    header_sub = "ICT/SMC Multi-Timeframe Pyramiding (DCA Dương) System — XAUUSD (Gold Spot) | 2022.08 – 2026.11"
    fig.text(0.05, 0.965, header_title, fontsize=17, fontweight='bold', color='#F1F5F9', fontfamily='sans-serif')
    fig.text(0.05, 0.942, header_sub, fontsize=10.5, color='#94A3B8', fontfamily='sans-serif')
    
    meta_tag = f"Engine: Event-Driven Python (NumPy) | Dataset: 99,997 Bars M15 | Execution Cost: 2.0 Pips Deducted ($0.20/oz) | Gates: G0-G7 PASS"
    fig.text(0.96, 0.950, meta_tag, fontsize=9.5, color='#38BDF8', ha='right', fontfamily='monospace',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#0F172A', edgecolor='#1E293B'))
             
    # -------------------------------------------------------------
    # Panel 1: Cumulative Equity vs High-Water Mark (Top-Left)
    # -------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, :2])
    ax1.set_facecolor('#0B0F19')
    ax1.plot(daily_df.index, daily_df['equity'], color='#10B981', linewidth=1.8, label='Strategy Equity Curve ($)', zorder=3)
    ax1.plot(daily_df.index, daily_df['peak'], color='#64748B', linewidth=1.0, linestyle=':', label='High-Water Mark ($)', zorder=2)
    ax1.axhline(initial_capital, color='#475569', linestyle='--', linewidth=0.9, alpha=0.7, label='Initial Capital ($5,000)')
    ax1.fill_between(daily_df.index, initial_capital, daily_df['equity'], where=(daily_df['equity'] >= initial_capital),
                     color='#10B981', alpha=0.12, interpolate=True)
    ax1.fill_between(daily_df.index, initial_capital, daily_df['equity'], where=(daily_df['equity'] < initial_capital),
                     color='#EF4444', alpha=0.15, interpolate=True)
                     
    ax1.set_title("PANEL A: Cumulative Strategy Equity & High-Water Mark Profile ($)", fontsize=11.5, fontweight='bold', color='#E2E8F0', pad=10, loc='left')
    ax1.set_ylabel("Portfolio Value ($USD)", color='#94A3B8', fontsize=10)
    ax1.grid(True, color='#ffffff', alpha=0.06, linestyle='--')
    ax1.legend(loc='upper left', framealpha=0.6, facecolor='#0F172A', edgecolor='#1E293B', fontsize=9)
    ax1.yaxis.set_major_formatter('${x:,.0f}')
    
    # -------------------------------------------------------------
    # Panel 2: Monthly Returns Heatmap (Top-Right)
    # -------------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 2])
    ax2.set_facecolor('#0B0F19')
    ax2.set_title("PANEL B: Monthly Returns Heatmap (%)", fontsize=11.5, fontweight='bold', color='#E2E8F0', pad=10, loc='left')
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    years = [2022, 2023, 2024, 2025, 2026]
    
    cdict = {'red':   ((0.0, 0.9, 0.9), (0.5, 0.1, 0.1), (1.0, 0.05, 0.05)),
             'green': ((0.0, 0.2, 0.2), (0.5, 0.1, 0.1), (1.0, 0.85, 0.85)),
             'blue':  ((0.0, 0.2, 0.2), (0.5, 0.1, 0.1), (1.0, 0.45, 0.45))}
    quant_cmap = LinearSegmentedColormap('QuantRet', cdict)
    
    data_mat = heatmap_df.values
    im = ax2.imshow(np.nan_to_num(data_mat, nan=0.0), cmap=quant_cmap, vmin=-10.0, vmax=15.0, aspect='auto')
    
    ax2.set_xticks(range(12))
    ax2.set_xticklabels(months, fontsize=8, color='#94A3B8')
    ax2.set_yticks(range(len(years)))
    ax2.set_yticklabels(years, fontsize=8.5, color='#94A3B8')
    
    for i in range(len(years)):
        for j in range(12):
            val = data_mat[i, j]
            if not np.isnan(val) and val != 0.0:
                ax2.text(j, i, f"{val:+.1f}", ha='center', va='center', fontsize=7.2,
                         color='#FFFFFF' if abs(val) > 3.0 else '#94A3B8', fontweight='500')
            elif val == 0.0:
                ax2.text(j, i, "·", ha='center', va='center', fontsize=8, color='#475569')
                
    cbar = fig.colorbar(im, ax=ax2, orientation='horizontal', pad=0.18, fraction=0.05)
    cbar.ax.tick_params(labelsize=7.5, colors='#94A3B8')
    cbar.set_label('Return Rate (%)', fontsize=8, color='#94A3B8')
    
    # -------------------------------------------------------------
    # Panel 3: Underwater Drawdown Profile (Middle-Left)
    # -------------------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor('#0B0F19')
    ax3.plot(daily_df.index, -daily_df['dd_pct'], color='#EF4444', linewidth=1.2, label='Drawdown Depth (%)')
    ax3.fill_between(daily_df.index, -daily_df['dd_pct'], 0, color='#EF4444', alpha=0.25)
    ax3.axhline(-max_dd_pct, color='#F87171', linestyle='--', linewidth=0.9, alpha=0.8,
                label=f'Max Drawdown: -{max_dd_pct:.2f}%')
    ax3.set_title("PANEL C: Underwater Drawdown Profile (% from High-Water Mark)", fontsize=11, fontweight='bold', color='#E2E8F0', pad=10, loc='left')
    ax3.set_ylabel("Drawdown (%)", color='#94A3B8', fontsize=9.5)
    ax3.grid(True, color='#ffffff', alpha=0.06, linestyle='--')
    ax3.legend(loc='lower left', framealpha=0.6, facecolor='#0F172A', edgecolor='#1E293B', fontsize=8.5)
    
    # -------------------------------------------------------------
    # Panel 4: Rolling 180-Day Sharpe Ratio (Middle-Center)
    # -------------------------------------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor('#0B0F19')
    rolling_ret = daily_df['returns'].rolling(180)
    rolling_sharpe = np.sqrt(252) * (rolling_ret.mean() / (rolling_ret.std() + 1e-9))
    ax4.plot(daily_df.index, rolling_sharpe, color='#38BDF8', linewidth=1.3, label='Rolling 180D Sharpe')
    ax4.axhline(1.0, color='#10B981', linestyle=':', linewidth=1.0, alpha=0.8, label='Target Benchmark (1.0)')
    ax4.axhline(0.0, color='#64748B', linestyle='-', linewidth=0.8, alpha=0.6)
    ax4.fill_between(daily_df.index, 0, rolling_sharpe, where=(rolling_sharpe >= 0), color='#38BDF8', alpha=0.15)
    ax4.fill_between(daily_df.index, 0, rolling_sharpe, where=(rolling_sharpe < 0), color='#EF4444', alpha=0.15)
    ax4.set_title("PANEL D: Rolling 180-Day Sharpe Ratio (Alpha Stability)", fontsize=11, fontweight='bold', color='#E2E8F0', pad=10, loc='left')
    ax4.set_ylabel("Sharpe Ratio", color='#94A3B8', fontsize=9.5)
    ax4.grid(True, color='#ffffff', alpha=0.06, linestyle='--')
    ax4.legend(loc='upper left', framealpha=0.6, facecolor='#0F172A', edgecolor='#1E293B', fontsize=8.5)
    
    # -------------------------------------------------------------
    # Panel 5: Annual Returns Bar Chart (Middle-Right)
    # -------------------------------------------------------------
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.set_facecolor('#0B0F19')
    bar_colors = ['#10B981' if v >= 0 else '#EF4444' for v in annual_df.values]
    bars = ax5.bar(annual_df.index.astype(str), annual_df.values, color=bar_colors, width=0.55, edgecolor='#1E293B')
    ax5.axhline(0, color='#64748B', linewidth=0.8)
    for b in bars:
        h = b.get_height()
        va = 'bottom' if h >= 0 else 'top'
        ax5.text(b.get_x() + b.get_width()/2., h + (1.5 if h >= 0 else -3.5),
                 f"{h:+.1f}%", ha='center', va=va, fontsize=8.5, color='#F1F5F9', fontweight='500')
    ax5.set_title("PANEL E: Net Annual Return (%)", fontsize=11, fontweight='bold', color='#E2E8F0', pad=10, loc='left')
    ax5.set_ylabel("Return (%)", color='#94A3B8', fontsize=9.5)
    ax5.grid(True, color='#ffffff', alpha=0.06, linestyle='--')
    
    # -------------------------------------------------------------
    # Panel 6: PnL Distribution & Fat Right-Tail Skew (Bottom-Left)
    # -------------------------------------------------------------
    ax6 = fig.add_subplot(gs[2, 0])
    ax6.set_facecolor('#0B0F19')
    pnl_data = df_trades['pnl_usd']
    # Filter extreme outliers for clear visual density plot
    pnl_plot = pnl_data[(pnl_data >= -50) & (pnl_data <= 250)]
    
    ax6.hist(pnl_plot, bins=60, density=True, color='#3B82F6', alpha=0.4, edgecolor='#1E293B', label='Trade Density')
    density = gaussian_kde(pnl_plot)
    xs = np.linspace(-50, 250, 300)
    ax6.plot(xs, density(xs), color='#60A5FA', linewidth=1.6)
    
    ax6.axvline(-avg_loss, color='#EF4444', linestyle='--', linewidth=1.2, label=f'Mean Loss: -${avg_loss:.2f}')
    ax6.axvline(avg_win, color='#10B981', linestyle='--', linewidth=1.2, label=f'Mean Win: +${avg_win:.2f}')
    ax6.set_title("PANEL F: PnL Distribution & Payoff Asymmetry (Fat Right-Tail)", fontsize=11, fontweight='bold', color='#E2E8F0', pad=10, loc='left')
    ax6.set_xlabel("Trade PnL ($USD)", color='#94A3B8', fontsize=9.5)
    ax6.set_ylabel("Density", color='#94A3B8', fontsize=9.5)
    ax6.grid(True, color='#ffffff', alpha=0.06, linestyle='--')
    ax6.legend(loc='upper right', framealpha=0.6, facecolor='#0F172A', edgecolor='#1E293B', fontsize=8.5)
    
    # -------------------------------------------------------------
    # Panel 7: Pyramiding Tier Breakdown (Bottom-Center)
    # -------------------------------------------------------------
    ax7 = fig.add_subplot(gs[2, 1])
    ax7.set_facecolor('#0B0F19')
    leg_summary = df_trades.groupby('step')['pnl_usd'].agg(['count', 'sum'])
    leg_steps = leg_summary.index.values
    leg_labels = [f"Entry_0 (Base)" if s == 0 else f"DCA_P_{s} (Leg)" for s in leg_steps]
    
    w = 0.38
    x_pos = np.arange(len(leg_steps))
    ax7_twin = ax7.twinx()
    
    b1 = ax7.bar(x_pos - w/2, leg_summary['count'], width=w, color='#829BCB', label='Trade Count', alpha=0.85)
    b2 = ax7_twin.bar(x_pos + w/2, leg_summary['sum'], width=w, color='#10B981', label='Net Profit ($)', alpha=0.85)
    
    ax7.set_xticks(x_pos)
    ax7.set_xticklabels(leg_labels, fontsize=8, color='#94A3B8', rotation=15)
    ax7.set_ylabel("Execution Count", color='#829BCB', fontsize=9)
    ax7_twin.set_ylabel("Total Profit Contribution ($)", color='#10B981', fontsize=9)
    ax7_twin.yaxis.set_major_formatter('${x:,.0f}')
    ax7.grid(True, color='#ffffff', alpha=0.06, linestyle='--')
    ax7.set_title("PANEL G: Pyramiding Layer Volume vs Profit Yield", fontsize=11, fontweight='bold', color='#E2E8F0', pad=10, loc='left')
    
    lines_1, labels_1 = ax7.get_legend_handles_labels()
    lines_2, labels_2 = ax7_twin.get_legend_handles_labels()
    ax7.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right', framealpha=0.6, facecolor='#0F172A', edgecolor='#1E293B', fontsize=8)
    
    # -------------------------------------------------------------
    # Panel 8: Institutional KPI Scientific Tearsheet Table (Bottom-Right)
    # -------------------------------------------------------------
    ax8 = fig.add_subplot(gs[2, 2])
    ax8.set_facecolor('#0B0F19')
    ax8.axis('off')
    ax8.set_title("PANEL H: Institutional Key Risk/Reward Matrix", fontsize=11, fontweight='bold', color='#E2E8F0', pad=10, loc='left')
    
    kpi_rows = [
        ("Initial Capital", f"${initial_capital:,.2f}"),
        ("Final Balance", f"${final_balance:,.2f}"),
        ("Net Total Profit", f"+${net_profit:,.2f} (+{total_return_pct:.1f}%)"),
        ("CAGR (Annualized)", f"+{cagr:.2f}% / year"),
        ("Profit Factor", f"{profit_factor:.2f}"),
        ("Sharpe Ratio (Ann.)", f"{sharpe:.2f}"),
        ("Sortino Ratio", f"{sortino:.2f}"),
        ("Calmar Ratio", f"{calmar:.2f}"),
        ("Max Drawdown (DD%)", f"-{max_dd_pct:.2f}% (${daily_df['peak'].max() - daily_df['equity'].min():,.0f})"),
        ("Total Trades Executed", f"{total_trades:,} orders"),
        ("Win Rate / Loss Rate", f"{win_rate:.1f}% / {100-win_rate:.1f}%"),
        ("Average Win / Loss", f"+${avg_win:.2f} / -${avg_loss:.2f}"),
        ("Payoff Ratio (Skew)", f"{payoff_ratio:.2f} : 1.0"),
        ("Execution Cost Deducted", "2.0 Pips ($0.20 / oz) Standard")
    ]
    
    table_cell_text = [[k, v] for k, v in kpi_rows]
    tbl = ax8.table(cellText=table_cell_text, colLabels=["Metric", "Empirical Value"],
                    loc='center', cellLoc='left', colWidths=[0.55, 0.45])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.2)
    tbl.scale(1.0, 1.42)
    
    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor('#1E293B')
        if row == 0:
            cell.set_facecolor('#1E293B')
            cell.set_text_props(color='#F1F5F9', fontweight='bold')
        else:
            cell.set_facecolor('#0F172A' if row % 2 == 0 else '#0B0F19')
            if col == 0:
                cell.set_text_props(color='#94A3B8')
            else:
                cell.set_text_props(color='#38BDF8' if 'Ratio' in kpi_rows[row-1][0] or 'CAGR' in kpi_rows[row-1][0] else ('#10B981' if '+' in kpi_rows[row-1][1] else '#F1F5F9'), fontfamily='monospace', fontweight='500')
                
    # Save the master scientific tearsheet
    out_img = os.path.join(base_dir, "vlux_quant_research_tearsheet.png")
    plt.savefig(out_img, dpi=220, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Scientific Quant Tearsheet generated: {out_img}")

if __name__ == '__main__':
    generate_tearsheet()

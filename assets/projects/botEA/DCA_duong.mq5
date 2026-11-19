//+------------------------------------------------------------------+
//|          Bot ICT/SMC Multi-TF Trend + CRT + FVG/OB + RSI + DCA   |
//|                    (Khung sườn - cần backtest & tinh chỉnh)      |
//+------------------------------------------------------------------+
#property copyright "You"
#property version   "2.00"
#property strict

//====================================================================
// ⚠️ TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM & CẢNH BÁO RỦI RO (LEGAL DISCLAIMER):
// 1. MÃ NGUỒN NÀY CHỈ PHỤC VỤ MỤC ĐÍCH NGHIÊN CỨU HỌC THUẬT & THAM KHẢO LẬP TRÌNH.
// 2. TUYỆT ĐỐI KHÔNG PHẢI LÀ LỜI KHUYÊN HOẶC KHUYẾN NGHỊ ĐẦU TƯ TÀI CHÍNH.
// 3. TÁC GIẢ KHÔNG CHỊU BẤT KỲ TRÁCH NHIỆM PHÁP LÝ HOẶC TÀI CHÍNH NÀO
//    ĐỐI VỚI BẤT KỲ TỔN THẤT NÀO PHÁT SINH TỪ VIỆC SỬ DỤNG MÃ NGUỒN NÀY.
// 4. GIAO DỊCH VÀNG (XAUUSD) ĐÒN BẨY CAO TIỀM ẨN NGUY CƠ RỦI RO RẤT LỚN.
//    KẾT QUẢ QUÁ KHỨ HOÀN TOÀN KHÔNG ĐẢM BẢO HIỆU SUẤT TRONG TƯƠNG LAI.
//====================================================================

enum ENUM_BIAS { BIAS_NONE = 0, BIAS_BUY = 1, BIAS_SELL = -1 };

//--- INPUTS CHUNG
input group "=== CHUNG ==="
input string   InpSymbol      = "XAUUSD";
input int      MagicNumber    = 20260712;
input int      Slippage       = 20;

//--- XU HUONG DA KHUNG
input group "=== XU HUONG DA KHUNG (D1 / H4 / H1) ==="
input int      EMA_Fast       = 20;
input int      EMA_Slow       = 50;

//--- CRT & LIQUIDITY
input group "=== CRT (Candle Range Theory) ==="
input int      CRT_SweepLookback = 5;   // so nen gan nhat de tim swing quet thanh khoan

//--- FVG / OB
input group "=== FVG / ORDER BLOCK ==="
input ENUM_TIMEFRAMES ZoneTF       = PERIOD_H1;
input int             ZoneLookback = 30;

//--- RSI
input group "=== RSI XAC NHAN (H1 / M30 / M15) ==="
input int      RSI_Period      = 14;
input double   RSI_Overbought  = 70;
input double   RSI_Oversold    = 30;

//--- ENTRY KHUNG NHO
input group "=== ENTRY KHUNG NHO ==="
input ENUM_TIMEFRAMES EntryTF     = PERIOD_M5;   // co the doi M15 / M1
input int              ATR_Period = 14;
input double           ATR_SL_Mult = 1.5;        // SL lenh dau tinh theo ATR
input double           TP_Pips      = 200;       // TP CO DINH (pip) cho lenh dau va moi lenh DCA
input double           RiskPerTrade = 1.0;       // % rui ro cho lenh goc

//--- DCA THEO PIP LOI NHUAN
input group "=== DCA DUONG (PYRAMIDING) THEO PIP ==="
input bool     UseDCA               = true;
input int      DCA_MaxSteps         = 5;     // so lenh DCA them toi da (chua tinh lenh goc)
input double   DCA_ProfitTriggerPips= 20;    // gia lai bao nhieu pip (tinh tu lenh gan nhat) thi mo them lenh
input double   DCA_TightSL_Pips     = 5;     // SL cho MOI lenh DCA moi = entry -/+ so pip nay
input double   DCA_LotMultiplier    = 1.0;   // 1.0 = lot bang nhau moi lenh DCA, >1 = tang dan
input double   PipSizeOverride      = 0.1;   // gia tri 1 pip (VD XAUUSD thuong = 0.1). Dat 0 de EA tu doan theo so chu so thap phan

//--- ZONE STRUCT
struct Zone
  {
   double top;
   double bottom;
   bool   valid;
  };

//--- HANDLES
int h_ema_fast_D1, h_ema_slow_D1;
int h_ema_fast_H4, h_ema_slow_H4;
int h_ema_fast_H1, h_ema_slow_H1;
int h_rsi_H1, h_rsi_M30, h_rsi_M15;
int h_atr_entry;

datetime g_lastBarTime = 0;

//+------------------------------------------------------------------+
int OnInit()
  {
   h_ema_fast_D1 = iMA(InpSymbol, PERIOD_D1, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
   h_ema_slow_D1 = iMA(InpSymbol, PERIOD_D1, EMA_Slow, 0, MODE_EMA, PRICE_CLOSE);
   h_ema_fast_H4 = iMA(InpSymbol, PERIOD_H4, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
   h_ema_slow_H4 = iMA(InpSymbol, PERIOD_H4, EMA_Slow, 0, MODE_EMA, PRICE_CLOSE);
   h_ema_fast_H1 = iMA(InpSymbol, PERIOD_H1, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
   h_ema_slow_H1 = iMA(InpSymbol, PERIOD_H1, EMA_Slow, 0, MODE_EMA, PRICE_CLOSE);

   h_rsi_H1  = iRSI(InpSymbol, PERIOD_H1,  RSI_Period, PRICE_CLOSE);
   h_rsi_M30 = iRSI(InpSymbol, PERIOD_M30, RSI_Period, PRICE_CLOSE);
   h_rsi_M15 = iRSI(InpSymbol, PERIOD_M15, RSI_Period, PRICE_CLOSE);

   h_atr_entry = iATR(InpSymbol, EntryTF, ATR_Period);

   if(h_ema_fast_D1==INVALID_HANDLE || h_ema_slow_D1==INVALID_HANDLE ||
      h_ema_fast_H4==INVALID_HANDLE || h_ema_slow_H4==INVALID_HANDLE ||
      h_ema_fast_H1==INVALID_HANDLE || h_ema_slow_H1==INVALID_HANDLE ||
      h_rsi_H1==INVALID_HANDLE || h_rsi_M30==INVALID_HANDLE || h_rsi_M15==INVALID_HANDLE ||
      h_atr_entry==INVALID_HANDLE)
     {
      Print("Loi tao handle chi bao. Kiem tra lai symbol/timeframe.");
      return(INIT_FAILED);
     }

   Print("Khoi tao thanh cong tat ca handle.");
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   IndicatorRelease(h_ema_fast_D1); IndicatorRelease(h_ema_slow_D1);
   IndicatorRelease(h_ema_fast_H4); IndicatorRelease(h_ema_slow_H4);
   IndicatorRelease(h_ema_fast_H1); IndicatorRelease(h_ema_slow_H1);
   IndicatorRelease(h_rsi_H1); IndicatorRelease(h_rsi_M30); IndicatorRelease(h_rsi_M15);
   IndicatorRelease(h_atr_entry);
  }

//+------------------------------------------------------------------+
//| Kiem tra nen moi tren khung entry (tranh xu ly lap lai trong nen)|
//+------------------------------------------------------------------+
bool IsNewBar()
  {
   datetime t = iTime(InpSymbol, EntryTF, 0);
   if(t != g_lastBarTime)
     {
      g_lastBarTime = t;
      return true;
     }
   return false;
  }

//+------------------------------------------------------------------+
//| Tinh gia tri 1 pip theo symbol (co the ghi de qua PipSizeOverride)|
//+------------------------------------------------------------------+
double GetPipSize()
  {
   if(PipSizeOverride > 0) return PipSizeOverride;
   int digits = (int)SymbolInfoInteger(InpSymbol, SYMBOL_DIGITS);
   double point = SymbolInfoDouble(InpSymbol, SYMBOL_POINT);
   if(digits==3 || digits==5) return point*10;
   return point;
  }

//+------------------------------------------------------------------+
//| Xu huong tong hop D1 + H4 + H1 (dung nen da dong - shift 1)      |
//+------------------------------------------------------------------+
ENUM_BIAS GetHTFBias()
  {
   double fD1[1], sD1[1], fH4[1], sH4[1], fH1[1], sH1[1];
   if(CopyBuffer(h_ema_fast_D1,0,1,1,fD1)<=0) return BIAS_NONE;
   if(CopyBuffer(h_ema_slow_D1,0,1,1,sD1)<=0) return BIAS_NONE;
   if(CopyBuffer(h_ema_fast_H4,0,1,1,fH4)<=0) return BIAS_NONE;
   if(CopyBuffer(h_ema_slow_H4,0,1,1,sH4)<=0) return BIAS_NONE;
   if(CopyBuffer(h_ema_fast_H1,0,1,1,fH1)<=0) return BIAS_NONE;
   if(CopyBuffer(h_ema_slow_H1,0,1,1,sH1)<=0) return BIAS_NONE;

   int score = 0;
   score += (fD1[0] > sD1[0]) ? 1 : -1;
   score += (fH4[0] > sH4[0]) ? 1 : -1;
   score += (fH1[0] > sH1[0]) ? 1 : -1;

   if(score >= 2) return BIAS_BUY;
   if(score <= -2) return BIAS_SELL;
   return BIAS_NONE;
  }

//+------------------------------------------------------------------+
//| CRT: kiem tra gia co quet thanh khoan qua dinh/day hom truoc     |
//| roi quay lai trong range khong (dau hieu dao chieu / manipulation)|
//+------------------------------------------------------------------+
ENUM_BIAS CheckCRT()
  {
   double pdh = iHigh(InpSymbol, PERIOD_D1, 1); // dinh hom truoc
   double pdl = iLow(InpSymbol,  PERIOD_D1, 1); // day hom truoc

   int idxLow  = iLowest(InpSymbol,  ZoneTF, MODE_LOW,  CRT_SweepLookback, 1);
   int idxHigh = iHighest(InpSymbol, ZoneTF, MODE_HIGH, CRT_SweepLookback, 1);
   double recentLow  = iLow(InpSymbol,  ZoneTF, idxLow);
   double recentHigh = iHigh(InpSymbol, ZoneTF, idxHigh);

   double curBid = SymbolInfoDouble(InpSymbol, SYMBOL_BID);
   double curAsk = SymbolInfoDouble(InpSymbol, SYMBOL_ASK);

   // quet day hom truoc roi hoi phuc len tren day -> thien huong BUY
   if(recentLow < pdl && curBid > pdl)
      return BIAS_BUY;

   // quet dinh hom truoc roi roi xuong duoi dinh -> thien huong SELL
   if(recentHigh > pdh && curAsk < pdh)
      return BIAS_SELL;

   return BIAS_NONE;
  }

//+------------------------------------------------------------------+
//| Tim Fair Value Gap gan nhat theo huong bias tren ZoneTF          |
//+------------------------------------------------------------------+
Zone FindFVG(ENUM_BIAS bias)
  {
   Zone z; z.valid=false; z.top=0; z.bottom=0;

   for(int i=2; i<ZoneLookback; i++)
     {
      double high2 = iHigh(InpSymbol, ZoneTF, i+2); // nen cu nhat trong bo 3
      double low2  = iLow(InpSymbol,  ZoneTF, i+2);
      double high0 = iHigh(InpSymbol, ZoneTF, i);   // nen gan nhat trong bo 3
      double low0  = iLow(InpSymbol,  ZoneTF, i);

      if(bias==BIAS_BUY)
        {
         // bullish FVG: day nen gan nhat > dinh nen cu nhat (co khoang trong)
         if(low0 > high2)
           {
            z.top = low0; z.bottom = high2; z.valid = true;
            return z;
           }
        }
      else if(bias==BIAS_SELL)
        {
         // bearish FVG: dinh nen gan nhat < day nen cu nhat
         if(high0 < low2)
           {
            z.top = low2; z.bottom = high0; z.valid = true;
            return z;
           }
        }
     }
   return z;
  }

//+------------------------------------------------------------------+
//| Tim Order Block gan nhat theo huong bias (don gian hoa)          |
//| BUY OB: nen giam ngay truoc 1 nen tang manh phá cấu trúc         |
//| SELL OB: nen tang ngay truoc 1 nen giam manh pha cau truc        |
//+------------------------------------------------------------------+
Zone FindOrderBlock(ENUM_BIAS bias)
  {
   Zone z; z.valid=false; z.top=0; z.bottom=0;

   for(int i=1; i<ZoneLookback; i++)
     {
      double o  = iOpen(InpSymbol,  ZoneTF, i);
      double c  = iClose(InpSymbol, ZoneTF, i);
      double o1 = iOpen(InpSymbol,  ZoneTF, i-1);
      double c1 = iClose(InpSymbol, ZoneTF, i-1);

      if(bias==BIAS_BUY)
        {
         bool downCandle = (c < o);
         bool nextBigUp  = (c1 > o1) && ((c1-o1) > MathAbs(c-o)*1.5);
         if(downCandle && nextBigUp)
           {
            z.top = MathMax(o,c); z.bottom = MathMin(o,c); z.valid = true;
            return z;
           }
        }
      else if(bias==BIAS_SELL)
        {
         bool upCandle    = (c > o);
         bool nextBigDown = (c1 < o1) && ((o1-c1) > MathAbs(c-o)*1.5);
         if(upCandle && nextBigDown)
           {
            z.top = MathMax(o,c); z.bottom = MathMin(o,c); z.valid = true;
            return z;
           }
        }
     }
   return z;
  }

//+------------------------------------------------------------------+
//| RSI da khung phai dong thuan voi bias                            |
//+------------------------------------------------------------------+
bool CheckRSIConfirmation(ENUM_BIAS bias)
  {
   double rH1[1], rM30[1], rM15[1];
   if(CopyBuffer(h_rsi_H1,0,1,1,rH1)<=0)   return false;
   if(CopyBuffer(h_rsi_M30,0,1,1,rM30)<=0) return false;
   if(CopyBuffer(h_rsi_M15,0,1,1,rM15)<=0) return false;

   if(bias==BIAS_BUY)
      return (rH1[0] > 50 && rM30[0] > 45 && rM15[0] < RSI_Overbought);
   if(bias==BIAS_SELL)
      return (rH1[0] < 50 && rM30[0] < 55 && rM15[0] > RSI_Oversold);
   return false;
  }

//+------------------------------------------------------------------+
//| Entry tren khung nho: gia phai cham vao Zone (FVG/OB) + co nen   |
//| xac nhan (engulfing) cung huong                                  |
//+------------------------------------------------------------------+
bool CheckEntryTrigger(ENUM_BIAS bias, Zone &zone)
  {
   if(!zone.valid) return false;

   double curLow  = iLow(InpSymbol,  EntryTF, 1);
   double curHigh = iHigh(InpSymbol, EntryTF, 1);
   double o  = iOpen(InpSymbol,  EntryTF, 1);
   double c  = iClose(InpSymbol, EntryTF, 1);
   double o2 = iOpen(InpSymbol,  EntryTF, 2);
   double c2 = iClose(InpSymbol, EntryTF, 2);

   bool touchedZone = (curLow <= zone.top && curHigh >= zone.bottom);
   if(!touchedZone) return false;

   if(bias==BIAS_BUY)
      return (c > o) && (c2 < o2) && (c > o2) && (o < c2);   // bullish engulfing
   if(bias==BIAS_SELL)
      return (c < o) && (c2 > o2) && (c < o2) && (o > c2);   // bearish engulfing

   return false;
  }

//+------------------------------------------------------------------+
//| Tinh lot theo % rui ro                                           |
//+------------------------------------------------------------------+
double CalcLotByRisk(double entry, double sl)
  {
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double volMin  = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MIN);
   if(balance <= 0) return(volMin);

   double riskMoney = balance * RiskPerTrade / 100.0;
   double slPoints  = MathAbs(entry - sl) / SymbolInfoDouble(InpSymbol, SYMBOL_POINT);
   if(slPoints <= 0) return(volMin);

   double tick_value = SymbolInfoDouble(InpSymbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_size  = SymbolInfoDouble(InpSymbol, SYMBOL_TRADE_TICK_SIZE);
   if(tick_value <= 0 || tick_size <= 0) return(volMin);

   double pointValuePerLot = (tick_value / tick_size) * SymbolInfoDouble(InpSymbol, SYMBOL_POINT);
   double riskPerLot = slPoints * pointValuePerLot;
   if(riskPerLot <= 0) return(volMin);

   double rawLots = riskMoney / riskPerLot;

   double volStep = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_STEP);
   double volMax  = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MAX);
   if(volStep <= 0) volStep = 0.01;
   if(volMin  <= 0) volMin  = 0.01;
   if(volMax  <= 0) volMax  = 100.0;

   double lots = MathFloor(rawLots / volStep) * volStep;
   if(lots < volMin) lots = volMin;
   if(lots > volMax) lots = volMax;
   return(lots);
  }

//+------------------------------------------------------------------+
//| Gui lenh chung                                                   |
//+------------------------------------------------------------------+
bool SendOrder(int type, double price, double sl, double tp, double lot, string cmt)
  {
   MqlTradeRequest req; MqlTradeResult res;
   ZeroMemory(req); ZeroMemory(res);

   req.action       = TRADE_ACTION_DEAL;
   req.symbol       = InpSymbol;
   req.volume       = lot;
   req.type         = (ENUM_ORDER_TYPE)type;
   req.price        = price;
   req.sl           = sl;
   req.tp           = tp;
   req.deviation    = Slippage;
   req.magic        = MagicNumber;
   req.type_filling = ORDER_FILLING_IOC;
   req.type_time    = ORDER_TIME_GTC;
   req.comment      = cmt;

   if(!OrderSend(req, res))
     {
      Print("OrderSend that bai, loi=", GetLastError());
      return false;
     }

   Print(TimeToString(TimeCurrent(),TIME_SECONDS), " | ", cmt,
         " ret=", res.retcode, " ticket=", res.order,
         " side=", (type==ORDER_TYPE_BUY?"BUY":"SELL"),
         " lot=", DoubleToString(lot,2),
         " SL=", DoubleToString(sl,_Digits),
         " TP=", DoubleToString(tp,_Digits));
   return true;
  }

//+------------------------------------------------------------------+
//| Mo lenh goc: SL theo ATR, TP CO DINH theo TP_Pips                |
//+------------------------------------------------------------------+
void OpenInitialTrade(ENUM_BIAS bias, double atr)
  {
   double pip = GetPipSize();
   int type = (bias==BIAS_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double entry = (type==ORDER_TYPE_BUY) ? SymbolInfoDouble(InpSymbol,SYMBOL_ASK)
                                          : SymbolInfoDouble(InpSymbol,SYMBOL_BID);
   double sl = (type==ORDER_TYPE_BUY) ? entry - atr*ATR_SL_Mult : entry + atr*ATR_SL_Mult;
   double tp = (type==ORDER_TYPE_BUY) ? entry + TP_Pips*pip : entry - TP_Pips*pip;
   double lot = CalcLotByRisk(entry, sl);

   // Neu lenh nay bi SL, coi nhu ket thuc chu ky - bot se cho tin hieu ICT moi
   // tren nen tiep theo, KHONG tu dong dao chieu hay mo lai.
   SendOrder(type, entry, sl, tp, lot, "Entry_0");
  }

//+------------------------------------------------------------------+
//| Kiem tra da co vi the mo cho symbol + magic nay chua              |
//+------------------------------------------------------------------+
bool HasOpenPosition()
  {
   for(int i=PositionsTotal()-1; i>=0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket<=0) continue;
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL)==InpSymbol &&
         PositionGetInteger(POSITION_MAGIC)==MagicNumber)
         return true;
     }
   return false;
  }

//+------------------------------------------------------------------+
//| Mo them 1 lenh DCA duong (pyramiding): SL chat (5 pip), TP co dinh|
//| (bang TP_Pips - giong lenh dau) - TAT CA lenh deu co du SL va TP  |
//+------------------------------------------------------------------+
void OpenProfitDCALeg(ENUM_BIAS dir, int stepIndex)
  {
   double pip = GetPipSize();
   int type = (dir==BIAS_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double entry = (type==ORDER_TYPE_BUY) ? SymbolInfoDouble(InpSymbol,SYMBOL_ASK)
                                          : SymbolInfoDouble(InpSymbol,SYMBOL_BID);
   double sl = (type==ORDER_TYPE_BUY) ? entry - DCA_TightSL_Pips*pip
                                       : entry + DCA_TightSL_Pips*pip;
   double tp = (type==ORDER_TYPE_BUY) ? entry + TP_Pips*pip
                                       : entry - TP_Pips*pip;

   double volMin = SymbolInfoDouble(InpSymbol, SYMBOL_VOLUME_MIN);
   double lot = volMin * MathPow(DCA_LotMultiplier, stepIndex);

   SendOrder(type, entry, sl, tp, lot, "DCA_P_" + IntegerToString(stepIndex));
  }

//+------------------------------------------------------------------+
//| Quan ly DCA duong theo pip loi nhuan.                            |
//| Neu lenh dau (hoac bat ky lenh nao) bi quet SL, EA KHONG tu dao   |
//| chieu hay mo lai - chu ky ket thuc, cho tin hieu ICT moi.        |
//+------------------------------------------------------------------+
void ManageDCA(ENUM_BIAS bias)
  {
   if(!UseDCA) return;

   int      count      = 0;
   long     curType    = -1;
   double   lastEntry  = 0;
   datetime lastTime   = 0;

   for(int i=PositionsTotal()-1; i>=0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket<=0) continue;
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL)!=InpSymbol) continue;
      if(PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;

      count++;
      long   type  = PositionGetInteger(POSITION_TYPE);
      double price = PositionGetDouble(POSITION_PRICE_OPEN);
      datetime t   = (datetime)PositionGetInteger(POSITION_TIME);

      if(t > lastTime) { lastTime = t; lastEntry = price; curType = type; }
     }

   if(count==0) return;              // chua co vi the nao dang mo (co the vua bi SL het - ket thuc chu ky)
   if(count > DCA_MaxSteps) return;  // du so lenh toi da roi

   ENUM_BIAS dir = (curType==POSITION_TYPE_BUY) ? BIAS_BUY : BIAS_SELL;

   // (tuy chon) chi DCA them khi bias ICT hien tai van dong thuan huong dang giu
   if(bias!=BIAS_NONE && dir!=bias) return;

   double pip = GetPipSize();
   double curPrice = (dir==BIAS_BUY) ? SymbolInfoDouble(InpSymbol,SYMBOL_BID)
                                      : SymbolInfoDouble(InpSymbol,SYMBOL_ASK);

   double profitPips = (dir==BIAS_BUY) ? (curPrice - lastEntry)/pip
                                        : (lastEntry - curPrice)/pip;

   if(profitPips >= DCA_ProfitTriggerPips)
      OpenProfitDCALeg(dir, count);
  }

//+------------------------------------------------------------------+
//| Expert tick                                                       |
//+------------------------------------------------------------------+
void OnTick()
  {
   // Quan ly DCA duong CHAY MOI TICK (khong doi nen moi)
   // vi gia co the dat nguong pip loi bat cu luc nao trong nen.
   ENUM_BIAS runningBias = BIAS_NONE;
   if(HasOpenPosition())
     {
      runningBias = GetHTFBias(); // dung de kiem tra "van dong thuan xu huong" khi DCA them
      ManageDCA(runningBias);
     }

   if(!IsNewBar()) return; // phan tim tin hieu entry MOI chi xu ly khi co nen moi tren EntryTF
   if(HasOpenPosition()) return; // da co vi the roi thi khong tim entry moi, chi quan ly DCA o tren

   ENUM_BIAS htfBias = GetHTFBias();
   ENUM_BIAS crtBias = CheckCRT();

   // Uu tien xu huong da khung, CRT dung de xac nhan them (khong mau thuan)
   ENUM_BIAS finalBias = BIAS_NONE;
   if(htfBias != BIAS_NONE && (crtBias == BIAS_NONE || crtBias == htfBias))
      finalBias = htfBias;
   else if(htfBias == BIAS_NONE && crtBias != BIAS_NONE)
      finalBias = crtBias;

   if(finalBias == BIAS_NONE) return;
   if(!CheckRSIConfirmation(finalBias)) return;

   Zone fvg = FindFVG(finalBias);
   Zone ob  = FindOrderBlock(finalBias);
   Zone zone = fvg.valid ? fvg : ob;   // uu tien FVG, khong co thi dung OB
   if(!zone.valid) return;

   double atrBuf[1];
   if(CopyBuffer(h_atr_entry, 0, 1, 1, atrBuf) <= 0) return;
   double atr = atrBuf[0];
   if(atr <= 0) return;

   if(CheckEntryTrigger(finalBias, zone))
      OpenInitialTrade(finalBias, atr);
  }
//+------------------------------------------------------------------+
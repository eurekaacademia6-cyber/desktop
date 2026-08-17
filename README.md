# Quotex Vision AI Desktop - Full Stack 2.0

Transparent Windows overlay for visual analysis of a visible Quotex-style chart.

## Six analysis layers

### Layer 1 - Candle Vision
- Open / High / Low / Close reconstruction
- body / wick ratio
- candle momentum
- consecutive candles
- rejection

### Layer 2 - Momentum
- RSI
- MACD
- Stochastic
- CCI
- Williams %R

### Layer 3 - Trend
- EMA 9 / 21 / 50 / 200
- ADX
- Ichimoku
- market structure

### Layer 4 - Volatility
- Bollinger Bands
- ATR
- volatility regime

### Layer 5 - Levels
- support / resistance
- supply / demand proxies
- VWAP proxy
- Fibonacci 38.2 / 50 / 61.8
- pivot points

### Layer 6 - Confirmation
- layer agreement
- trend + momentum agreement
- volume gate
- multi-timeframe gate
- strict NO TRADE filter

## Data honesty

This desktop app reads only visible screen pixels.

True broker volume is not available from those pixels, so the app does not
pretend pseudo-volume is real volume.

True multi-timeframe confirmation is not available from one chart ROI, so that
confirmation is also treated as unavailable unless a future multi-chart capture
module is added.

This is intentionally conservative.

## Run

PowerShell:

```powershell
py -m venv .venv
.venv\Scriptsctivate
pip install -r requirements.txt
python main.py
```

Open Quotex first and then start the overlay.


## One-click Windows installation
The preferred release is the generated `QuotexVisionAI-Setup.exe` installer. It bundles the Python runtime and all dependencies through PyInstaller. End users do not need to install Python.

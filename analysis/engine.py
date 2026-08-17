from __future__ import annotations

import numpy as np

from analysis.indicators import build_snapshot
from vision.models import AnalysisComponent, Candle, Signal


def sigmoid(x):
    if x >= 0:
        e = np.exp(-x)
        return float(1.0 / (1.0 + e))
    e = np.exp(x)
    return float(e / (1.0 + e))


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


class AnalysisEngine:
    def analyze(
        self,
        candles,
        quality,
        horizon_seconds=60,
        volume_available=False,
        higher_tf_available=False,
    ):
        if len(candles) < 10:
            return Signal(
                "NO TRADE", 0.50, 0.0, 0.0,
                blocked_reason="Fewer than 10 candles detected.",
                no_trade_reasons=["INSUFFICIENT_CANDLES"],
            )

        if quality < 0.60:
            return Signal(
                "NO TRADE", 0.50, 0.0, 0.0,
                blocked_reason="Vision quality is below threshold.",
                no_trade_reasons=["LOW_VISION_QUALITY"],
            )

        s = build_snapshot(candles)
        last = candles[-1]
        avg_range = max(1.0, float(np.mean([c.range_px for c in candles[-10:]])))

        components = []

        # L1 Candle Vision
        candle_score = (
            1.15 * (0.75 if last.bullish else -0.75)
            + 0.65 * s.candle_momentum
            + 0.55 * s.rejection_score
            + 0.45 * s.candle_pattern_score
        )
        if s.consecutive_bullish >= 3:
            candle_score += 0.25
        if s.consecutive_bearish >= 3:
            candle_score -= 0.25

        components.append(AnalysisComponent(
            "L1 Candle Vision",
            sigmoid(candle_score),
            1.25,
            "OHLC body/wick, momentum, streak, rejection",
        ))

        # L2 Momentum
        momentum = 0.0

        if s.rsi is not None:
            momentum += clamp((s.rsi - 50.0) / 20.0, -1.5, 1.5) * 0.70

        if s.macd_hist is not None:
            momentum += clamp(s.macd_hist / avg_range, -2.0, 2.0) * 0.45

        if s.stochastic_k is not None and s.stochastic_d is not None:
            momentum += clamp((s.stochastic_k - s.stochastic_d) / 25.0, -1.0, 1.0) * 0.45

        if s.cci is not None:
            momentum += clamp(s.cci / 200.0, -1.0, 1.0) * 0.35

        if s.williams_r is not None:
            momentum += clamp((s.williams_r + 50.0) / 50.0, -1.0, 1.0) * 0.25

        components.append(AnalysisComponent(
            "L2 Momentum",
            sigmoid(momentum),
            1.20,
            "RSI, MACD, Stochastic, CCI, Williams %R",
        ))

        # L3 Trend
        trend = 0.0
        for value, weight in [
            (s.ema9, 0.35),
            (s.ema21, 0.30),
            (s.ema50, 0.20),
            (s.ema200, 0.15),
        ]:
            if value is not None:
                trend += weight * clamp(
                    (last.close_px - value) / avg_range,
                    -2.0, 2.0,
                )

        if s.adx is not None and s.adx >= 20:
            if s.ema9 is not None and s.ema21 is not None:
                trend += 0.30 * (1.0 if s.ema9 > s.ema21 else -1.0)

        if s.ichimoku_span_a is not None and s.ichimoku_span_b is not None:
            top = max(s.ichimoku_span_a, s.ichimoku_span_b)
            bottom = min(s.ichimoku_span_a, s.ichimoku_span_b)
            if last.close_px > top:
                trend += 0.40
            elif last.close_px < bottom:
                trend -= 0.40

        if s.structure == "HH_HL_BULL":
            trend += 0.75
        elif s.structure == "LH_LL_BEAR":
            trend -= 0.75

        components.append(AnalysisComponent(
            "L3 Trend",
            sigmoid(trend),
            1.30,
            "EMA 9/21/50/200, ADX, Ichimoku, market structure",
        ))

        # L4 Volatility
        vol = 0.0
        if s.volatility_regime == "EXPANSION":
            vol += 0.15 * np.sign(s.candle_momentum)

        if s.bb_upper is not None and s.bb_lower is not None:
            if last.close_px > s.bb_upper:
                vol += 0.20 * np.sign(s.candle_momentum)
            elif last.close_px < s.bb_lower:
                vol += 0.20 * np.sign(s.candle_momentum)

        components.append(AnalysisComponent(
            "L4 Volatility",
            sigmoid(vol),
            0.80,
            "Bollinger Bands, ATR, volatility regime",
        ))

        # L5 Levels
        level = 0.0

        if s.support is not None and s.resistance is not None:
            ds = abs(last.close_px - s.support)
            dr = abs(last.close_px - s.resistance)
            if ds < dr * 0.40:
                level += 0.55
            elif dr < ds * 0.40:
                level -= 0.55

        if s.demand_zone is not None:
            lo, hi = s.demand_zone
            if lo <= last.close_px <= hi:
                level += 0.55

        if s.supply_zone is not None:
            lo, hi = s.supply_zone
            if lo <= last.close_px <= hi:
                level -= 0.55

        if s.vwap is not None:
            level += 0.25 * np.sign(last.close_px - s.vwap)

        for fib in (s.fib_382, s.fib_500, s.fib_618):
            if fib is not None and abs(last.close_px - fib) <= avg_range * 0.20:
                level += 0.08 * np.sign(s.candle_momentum)

        if s.pivot is not None:
            level += 0.20 * np.sign(last.close_px - s.pivot)

        components.append(AnalysisComponent(
            "L5 Levels",
            sigmoid(level),
            0.95,
            "S/R, supply/demand, VWAP proxy, Fibonacci, pivots",
        ))

        # L6 Confirmation
        probs = [c.probability_up for c in components]
        weights = [c.weight for c in components]
        p_up = float(np.average(probs, weights=weights))
        up = p_up >= 0.5
        agreement = sum(((p >= 0.5) == up) for p in probs) / len(probs)

        trend_prob = components[2].probability_up
        momentum_prob = components[1].probability_up
        trend_momentum_agree = ((trend_prob >= 0.5) == (momentum_prob >= 0.5))

        edge = abs(p_up - 0.5) * 2.0
        confidence = clamp(
            0.36 * edge
            + 0.32 * agreement
            + 0.20 * quality
            + (0.12 if trend_momentum_agree else 0.0),
            0.0, 1.0,
        )

        # Missing true data is never fabricated.
        no_trade = []

        if not volume_available:
            no_trade.append("VOLUME_UNAVAILABLE")
        if not higher_tf_available:
            no_trade.append("MTF_UNAVAILABLE")
        if not trend_momentum_agree:
            no_trade.append("TREND_MOMENTUM_CONFLICT")
        if edge < 0.24:
            no_trade.append("EDGE_TOO_SMALL")
        if agreement < 0.70:
            no_trade.append("LAYER_DISAGREEMENT")
        if confidence < 0.66:
            no_trade.append("CONFIDENCE_GATE")

        label = "NO TRADE"

        if (
            confidence >= 0.66
            and agreement >= 0.70
            and edge >= 0.24
            and trend_momentum_agree
        ):
            label = "UP" if up else "DOWN"

        reasons = [
            f"{c.name}: {'UP' if c.probability_up >= 0.5 else 'DOWN'} {c.probability_up*100:.0f}%"
            for c in components
        ]
        reasons.append(f"Structure: {s.structure}")
        reasons.append(f"Volatility: {s.volatility_regime}")
        if s.adx is not None:
            reasons.append(f"ADX: {s.adx:.1f}")
        if s.rsi is not None:
            reasons.append(f"RSI: {s.rsi:.1f}")

        return Signal(
            label=label,
            up_probability=p_up,
            confidence=confidence,
            agreement=agreement,
            components=components,
            reasons=reasons,
            no_trade_reasons=no_trade,
        )

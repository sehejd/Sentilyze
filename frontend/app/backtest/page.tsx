"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, Plus, Trash2, Play, Loader2, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  fetchBacktestIndicators,
  runBacktest,
  BacktestIndicatorsResponse,
  BacktestRule,
  BacktestResponse,
  FundamentalGateCheck,
} from "@/lib/api";

const OPERATOR_LABELS: Record<string, string> = {
  "<": "<", "<=": "≤", ">": ">", ">=": "≥", "==": "=",
  crosses_above: "crosses above", crosses_below: "crosses below",
};

function emptyRule(): BacktestRule {
  return { field: "close", operator: "<", value: 0 };
}

function emptyCheck(): FundamentalGateCheck {
  return { metric: "pe_ratio", operator: "<", value: 25 };
}

function RuleRow({
  rule, indicatorsMeta, onChange, onRemove,
}: {
  rule: BacktestRule;
  indicatorsMeta: BacktestIndicatorsResponse | null;
  onChange: (rule: BacktestRule) => void;
  onRemove: () => void;
}) {
  const fields = indicatorsMeta ? Object.keys(indicatorsMeta.indicators) : ["close"];
  const isCrossOperator = rule.operator === "crosses_above" || rule.operator === "crosses_below";

  return (
    <div className="flex flex-wrap items-center gap-2 p-2 bg-white rounded border border-beige">
      <select
        className="text-xs border border-beige rounded px-2 py-1.5 bg-white text-dark"
        value={rule.field}
        onChange={(e) => onChange({ ...rule, field: e.target.value })}
      >
        {fields.map((f) => (
          <option key={f} value={f}>{indicatorsMeta?.indicators[f]?.label || f}</option>
        ))}
      </select>

      <select
        className="text-xs border border-beige rounded px-2 py-1.5 bg-white text-dark"
        value={rule.operator}
        onChange={(e) => onChange({ ...rule, operator: e.target.value as BacktestRule["operator"] })}
      >
        {(indicatorsMeta?.operators || Object.keys(OPERATOR_LABELS)).map((op) => (
          <option key={op} value={op}>{OPERATOR_LABELS[op] || op}</option>
        ))}
      </select>

      {isCrossOperator ? (
        <select
          className="text-xs border border-beige rounded px-2 py-1.5 bg-white text-dark"
          value={typeof rule.value === "string" ? rule.value : "close"}
          onChange={(e) => onChange({ ...rule, value: e.target.value })}
        >
          {fields.map((f) => (
            <option key={f} value={f}>{indicatorsMeta?.indicators[f]?.label || f}</option>
          ))}
        </select>
      ) : (
        <Input
          type="number"
          className="w-24 h-8 text-xs"
          value={typeof rule.value === "number" ? rule.value : 0}
          onChange={(e) => onChange({ ...rule, value: parseFloat(e.target.value) || 0 })}
        />
      )}

      <button onClick={onRemove} className="ml-auto text-grayish hover:text-accent-red">
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

export default function BacktestPage() {
  const [indicatorsMeta, setIndicatorsMeta] = useState<BacktestIndicatorsResponse | null>(null);

  const [ticker, setTicker] = useState("AAPL");
  const [start, setStart] = useState("2022-01-01");
  const [end, setEnd] = useState("");
  const [initialCapital, setInitialCapital] = useState("10000");
  const [positionSizePct, setPositionSizePct] = useState("100");
  const [stopLossPct, setStopLossPct] = useState("");
  const [takeProfitPct, setTakeProfitPct] = useState("");

  const [entryRules, setEntryRules] = useState<BacktestRule[]>([{ field: "rsi_14", operator: "<", value: 30 }]);
  const [exitRules, setExitRules] = useState<BacktestRule[]>([{ field: "rsi_14", operator: ">", value: 70 }]);

  const [fundamentalGateEnabled, setFundamentalGateEnabled] = useState(false);
  const [fundamentalChecks, setFundamentalChecks] = useState<FundamentalGateCheck[]>([emptyCheck()]);

  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBacktestIndicators().then(setIndicatorsMeta).catch(() => setIndicatorsMeta(null));
  }, []);

  const handleRun = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await runBacktest({
        ticker,
        start,
        end: end || undefined,
        entry_rules: entryRules,
        exit_rules: exitRules,
        initial_capital: parseFloat(initialCapital) || 10000,
        position_size_pct: (parseFloat(positionSizePct) || 100) / 100,
        stop_loss_pct: stopLossPct ? parseFloat(stopLossPct) : undefined,
        take_profit_pct: takeProfitPct ? parseFloat(takeProfitPct) : undefined,
        fundamental_gate: fundamentalGateEnabled
          ? { enabled: true, checks: fundamentalChecks }
          : undefined,
      });
      if (!response.success) {
        setError(response.error || "Backtest failed");
      } else {
        setResult(response);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Backtest request failed");
    } finally {
      setIsLoading(false);
    }
  }, [ticker, start, end, entryRules, exitRules, initialCapital, positionSizePct, stopLossPct, takeProfitPct, fundamentalGateEnabled, fundamentalChecks]);

  const chartData = result
    ? result.equity_curve.map((pt, i) => ({
        date: pt.date,
        strategy: pt.equity,
        buyHold: result.buy_hold_equity_curve[i]?.equity,
      }))
    : [];

  const fundamentalMetricKeys = indicatorsMeta ? Object.keys(indicatorsMeta.fundamental_metrics) : [];

  return (
    <div className="min-h-screen bg-light px-6 py-10">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-grayish hover:text-dark">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-dark">Backtesting Panel</h1>
            <p className="text-sm text-grayish">
              Simulate a rule-based strategy over real historical price data
            </p>
          </div>
        </div>

        {/* Configuration */}
        <Card className="bg-light border-beige">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold text-dark">Strategy Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
              <div className="col-span-2 md:col-span-1">
                <label className="text-xs text-grayish">Ticker</label>
                <Input value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} className="h-8 text-sm" />
              </div>
              <div>
                <label className="text-xs text-grayish">Start</label>
                <Input type="date" value={start} onChange={(e) => setStart(e.target.value)} className="h-8 text-sm" />
              </div>
              <div>
                <label className="text-xs text-grayish">End (optional)</label>
                <Input type="date" value={end} onChange={(e) => setEnd(e.target.value)} className="h-8 text-sm" />
              </div>
              <div>
                <label className="text-xs text-grayish">Capital ($)</label>
                <Input type="number" value={initialCapital} onChange={(e) => setInitialCapital(e.target.value)} className="h-8 text-sm" />
              </div>
              <div>
                <label className="text-xs text-grayish">Position size (%)</label>
                <Input type="number" value={positionSizePct} onChange={(e) => setPositionSizePct(e.target.value)} className="h-8 text-sm" />
              </div>
              <div>
                <label className="text-xs text-grayish">Stop loss (%)</label>
                <Input type="number" placeholder="none" value={stopLossPct} onChange={(e) => setStopLossPct(e.target.value)} className="h-8 text-sm" />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-dark">Entry rules (all must be true to buy)</h3>
                <Button size="sm" variant="outline" onClick={() => setEntryRules([...entryRules, emptyRule()])}>
                  <Plus className="w-3.5 h-3.5" /> Add rule
                </Button>
              </div>
              <div className="space-y-2">
                {entryRules.map((rule, i) => (
                  <RuleRow
                    key={i}
                    rule={rule}
                    indicatorsMeta={indicatorsMeta}
                    onChange={(r) => setEntryRules(entryRules.map((existing, idx) => (idx === i ? r : existing)))}
                    onRemove={() => setEntryRules(entryRules.filter((_, idx) => idx !== i))}
                  />
                ))}
                {entryRules.length === 0 && <p className="text-xs text-grayish">No entry rules - add at least one.</p>}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-dark">Exit rules (any true sells the position)</h3>
                <Button size="sm" variant="outline" onClick={() => setExitRules([...exitRules, emptyRule()])}>
                  <Plus className="w-3.5 h-3.5" /> Add rule
                </Button>
              </div>
              <div className="space-y-2">
                {exitRules.map((rule, i) => (
                  <RuleRow
                    key={i}
                    rule={rule}
                    indicatorsMeta={indicatorsMeta}
                    onChange={(r) => setExitRules(exitRules.map((existing, idx) => (idx === i ? r : existing)))}
                    onRemove={() => setExitRules(exitRules.filter((_, idx) => idx !== i))}
                  />
                ))}
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    placeholder="Take profit % (optional)"
                    value={takeProfitPct}
                    onChange={(e) => setTakeProfitPct(e.target.value)}
                    className="h-8 text-xs w-56"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-dark mb-2">
                <input
                  type="checkbox"
                  checked={fundamentalGateEnabled}
                  onChange={(e) => setFundamentalGateEnabled(e.target.checked)}
                />
                Fundamental gate (static filter on current fundamentals - not a per-day historical filter)
              </label>
              {fundamentalGateEnabled && (
                <div className="space-y-2">
                  {fundamentalChecks.map((check, i) => (
                    <div key={i} className="flex flex-wrap items-center gap-2 p-2 bg-white rounded border border-beige">
                      <select
                        className="text-xs border border-beige rounded px-2 py-1.5 bg-white text-dark"
                        value={check.metric}
                        onChange={(e) => {
                          const updated = [...fundamentalChecks];
                          updated[i] = { ...check, metric: e.target.value };
                          setFundamentalChecks(updated);
                        }}
                      >
                        {fundamentalMetricKeys.map((m) => <option key={m} value={m}>{m}</option>)}
                      </select>
                      <select
                        className="text-xs border border-beige rounded px-2 py-1.5 bg-white text-dark"
                        value={check.operator}
                        onChange={(e) => {
                          const updated = [...fundamentalChecks];
                          updated[i] = { ...check, operator: e.target.value as FundamentalGateCheck["operator"] };
                          setFundamentalChecks(updated);
                        }}
                      >
                        {["<", "<=", ">", ">=", "=="].map((op) => <option key={op} value={op}>{OPERATOR_LABELS[op]}</option>)}
                      </select>
                      <Input
                        type="number"
                        className="w-24 h-8 text-xs"
                        value={check.value}
                        onChange={(e) => {
                          const updated = [...fundamentalChecks];
                          updated[i] = { ...check, value: parseFloat(e.target.value) || 0 };
                          setFundamentalChecks(updated);
                        }}
                      />
                      <button
                        onClick={() => setFundamentalChecks(fundamentalChecks.filter((_, idx) => idx !== i))}
                        className="ml-auto text-grayish hover:text-accent-red"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                  <Button size="sm" variant="outline" onClick={() => setFundamentalChecks([...fundamentalChecks, emptyCheck()])}>
                    <Plus className="w-3.5 h-3.5" /> Add check
                  </Button>
                </div>
              )}
            </div>

            <Button onClick={handleRun} disabled={isLoading} className="bg-dark text-white hover:bg-dark/90">
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              Run Backtest
            </Button>
          </CardContent>
        </Card>

        {error && (
          <Alert className="border-accent-red bg-red-50">
            <AlertCircle className="h-4 w-4 text-accent-red" />
            <AlertDescription className="text-dark">{error}</AlertDescription>
          </Alert>
        )}

        {result && (
          <div className="space-y-4">
            <Card className="bg-light border-beige">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold text-dark">
                  Results: {result.ticker} ({result.period.start} → {result.period.end})
                </CardTitle>
                {result.entry_gate.note && (
                  <CardDescription className="text-xs text-grayish">{result.entry_gate.note}</CardDescription>
                )}
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  {[
                    { label: "Total Return", value: `${result.stats.total_return_pct}%` },
                    { label: "CAGR", value: `${result.stats.cagr_pct}%` },
                    { label: "Max Drawdown", value: `${result.stats.max_drawdown_pct}%` },
                    { label: "Sharpe Ratio", value: result.stats.sharpe_ratio ?? "N/A" },
                    { label: "Trades", value: result.stats.num_trades },
                    { label: "Win Rate", value: result.stats.win_rate_pct !== null ? `${result.stats.win_rate_pct}%` : "N/A" },
                    { label: "Buy & Hold Return", value: `${result.stats.buy_hold_return_pct}%` },
                    { label: "Alpha vs Buy & Hold", value: `${result.stats.alpha_vs_buy_hold_pct}%` },
                  ].map((stat) => (
                    <div key={stat.label} className="p-3 bg-white rounded border border-beige text-center">
                      <p className="text-[11px] text-grayish">{stat.label}</p>
                      <p className="text-lg font-bold text-dark">{stat.value}</p>
                    </div>
                  ))}
                </div>

                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ccc5b9" />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} minTickGap={40} />
                      <YAxis tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="strategy" name="Strategy" stroke="#eb5e28" dot={false} strokeWidth={2} />
                      <Line type="monotone" dataKey="buyHold" name="Buy & Hold" stroke="#403d39" dot={false} strokeWidth={1.5} strokeDasharray="4 4" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <p className="text-[11px] text-grayish mt-3">{result.fundamental_gate_limitation}</p>
              </CardContent>
            </Card>

            <Card className="bg-light border-beige">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold text-dark">Trade Log ({result.trades.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="max-h-80 overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-left text-grayish border-b border-beige">
                        <th className="py-1.5 pr-3">Date</th>
                        <th className="py-1.5 pr-3">Action</th>
                        <th className="py-1.5 pr-3">Price</th>
                        <th className="py-1.5 pr-3">Shares</th>
                        <th className="py-1.5 pr-3">Return</th>
                        <th className="py-1.5 pr-3">Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.trades.map((trade, i) => (
                        <tr key={i} className="border-b border-beige/50">
                          <td className="py-1.5 pr-3 text-dark">{trade.date}</td>
                          <td className="py-1.5 pr-3">
                            <span className={trade.action === "buy" ? "text-green-600 font-medium" : "text-accent-red font-medium"}>
                              {trade.action.toUpperCase()}
                            </span>
                          </td>
                          <td className="py-1.5 pr-3 text-dark">${trade.price}</td>
                          <td className="py-1.5 pr-3 text-dark">{trade.shares}</td>
                          <td className="py-1.5 pr-3 text-dark">{trade.return_pct !== undefined ? `${trade.return_pct}%` : "—"}</td>
                          <td className="py-1.5 pr-3 text-grayish">{trade.reason || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, Calculator, Loader2, AlertCircle, TrendingUp, TrendingDown, Minus, ChevronDown, ChevronUp, Brain } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from "recharts";
import {
  fetchValuation,
  fetchPeerPerformance,
  ValuationResponse,
  ValuationMethodResult,
  PeerPerformanceResponse,
} from "@/lib/api";

const METHOD_LABELS: Record<string, string> = {
  dcf: "Discounted Cash Flow",
  comparable_company_analysis: "Comparable Company Analysis",
  ddm: "Dividend Discount Model",
  graham_number: "Graham Number",
  asset_based: "Asset-Based (Book Value)",
};

const METHOD_EXPLAINERS: Record<string, string> = {
  dcf: "Projects future free cash flows and discounts them back to today's dollars using a risk-adjusted rate (WACC). Sensitive to growth and discount-rate assumptions - best for mature, cash-generative businesses.",
  comparable_company_analysis: "Applies the sector's median trading multiples (P/E, EV/EBITDA, etc.) to this company's own fundamentals. Reflects what the market is currently paying for similar businesses, not intrinsic value.",
  ddm: "Values the stock as the present value of expected future dividends. Only meaningful for companies with an established, sustained dividend history.",
  graham_number: "Benjamin Graham's conservative formula: sqrt(22.5 x EPS x Book Value per Share). A quick sanity-check floor value, not a full valuation - ignores growth and cash flow entirely.",
  asset_based: "Values the company at its net tangible assets (book value), i.e. what would be left if it liquidated today. A floor estimate that ignores earning power - most relevant for asset-heavy or distressed companies.",
};

const METHOD_COLORS: Record<string, string> = {
  dcf: "#eb5e28",
  comparable_company_analysis: "#2f6690",
  ddm: "#0ca30c",
  graham_number: "#8a5cf6",
  asset_based: "#c9a227",
};

const RATING_STYLES: Record<string, { color: string; label: string }> = {
  undervalued: { color: "bg-green-500", label: "Undervalued" },
  overvalued: { color: "bg-accent-red", label: "Overvalued" },
  fairly_valued: { color: "bg-yellow-400", label: "Fairly Valued" },
  insufficient_data: { color: "bg-beige", label: "Insufficient Data" },
};

function formatAssumptionValue(value: unknown): string {
  if (typeof value === "number") {
    return Math.abs(value) < 1 ? `${(value * 100).toFixed(2)}%` : value.toLocaleString();
  }
  if (Array.isArray(value)) return value.join(", ");
  if (value && typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function MethodCard({ method }: { method: ValuationMethodResult }) {
  const [expanded, setExpanded] = useState(false);
  const upside = method.upside_pct;

  return (
    <Card className="bg-light border-beige">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold text-dark">{METHOD_LABELS[method.method] || method.method}</CardTitle>
          {method.applicable ? (
            upside !== undefined && upside !== null && (
              <Badge className={upside >= 0 ? "bg-green-500 text-white" : "bg-accent-red text-white"}>
                {upside >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                {upside >= 0 ? "+" : ""}{upside}%
              </Badge>
            )
          ) : (
            <Badge className="bg-beige text-dark">N/A</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {method.applicable ? (
          <>
            <p className="text-2xl font-bold text-dark">${method.fair_value_per_share}</p>
            <p className="text-xs text-grayish">vs current ${method.current_price}</p>
          </>
        ) : (
          <p className="text-xs text-grayish">{method.note}</p>
        )}
        {METHOD_EXPLAINERS[method.method] && (
          <p className="text-[11px] text-grayish mt-2 leading-relaxed">{METHOD_EXPLAINERS[method.method]}</p>
        )}
        {method.applicable && (
          <>
            <p className="text-xs text-grayish mt-2">{method.note}</p>
            {method.assumptions && (
              <div className="mt-2">
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="flex items-center gap-1 text-[11px] text-grayish hover:text-dark"
                >
                  {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  Assumptions
                </button>
                {expanded && (
                  <div className="mt-1.5 space-y-1 p-2 bg-white rounded border border-beige">
                    {Object.entries(method.assumptions)
                      .filter(([k]) => k !== "peers_used" && k !== "implied_values_by_multiple")
                      .map(([key, value]) => (
                        <div key={key} className="flex justify-between text-[11px]">
                          <span className="text-grayish">{key.replace(/_/g, " ")}</span>
                          <span className="text-dark font-medium">{formatAssumptionValue(value)}</span>
                        </div>
                      ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default function ValuationPage() {
  const [ticker, setTicker] = useState("AAPL");
  const [valuation, setValuation] = useState<ValuationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [peerPerformance, setPeerPerformance] = useState<PeerPerformanceResponse | null>(null);
  const [isLoadingPeers, setIsLoadingPeers] = useState(false);
  const [peerError, setPeerError] = useState<string | null>(null);

  const handleAnalyze = useCallback(async () => {
    if (!ticker.trim()) return;
    setIsLoading(true);
    setError(null);
    setValuation(null);
    setPeerPerformance(null);
    setPeerError(null);
    try {
      const result = await fetchValuation(ticker);
      if (!result.success) {
        setError(result.error || "Valuation failed");
      } else {
        setValuation(result);
      }
    } catch {
      setError(`Failed to fetch valuation for ${ticker.toUpperCase()}`);
    } finally {
      setIsLoading(false);
    }
  }, [ticker]);

  const handleRunPeerPerformance = useCallback(async () => {
    setIsLoadingPeers(true);
    setPeerError(null);
    try {
      const result = await fetchPeerPerformance(ticker, 12);
      if (!result.success) {
        setPeerError(result.error || "Peer performance analysis failed");
      } else {
        setPeerPerformance(result);
      }
    } catch {
      setPeerError("Failed to run peer performance analysis - this fits a model across ~10-15 sector peers and can take a minute.");
    } finally {
      setIsLoadingPeers(false);
    }
  }, [ticker]);

  const rating = valuation ? RATING_STYLES[valuation.rating] || RATING_STYLES.insufficient_data : null;

  const fairValueChartData = valuation
    ? [
        {
          name: "Current Price",
          value: valuation.current_price,
          fill: "#3a3835",
        },
        ...valuation.methods
          .filter((m) => m.applicable && m.fair_value_per_share !== null && m.fair_value_per_share !== undefined)
          .map((m) => ({
            name: METHOD_LABELS[m.method] || m.method,
            value: m.fair_value_per_share as number,
            fill: METHOD_COLORS[m.method] || "#8a8580",
          })),
        ...(valuation.blended_fair_value_per_share !== null
          ? [{ name: "Blended", value: valuation.blended_fair_value_per_share, fill: "#111827" }]
          : []),
      ]
    : [];

  const coefficientChartData = peerPerformance
    ? peerPerformance.model.coefficients.map((c) => ({ name: c.label, value: c.coefficient }))
    : [];

  return (
    <div className="min-h-screen bg-light px-6 py-10">
      <div className="max-w-6xl mx-auto space-y-4">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-grayish hover:text-dark">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-dark flex items-center gap-2">
              <Calculator className="w-7 h-7 text-accent-red" />
              Valuation Calculator
            </h1>
            <p className="text-sm text-grayish">
              Five independent fundamental valuation methods, plus a peer-performance model
            </p>
          </div>
        </div>

        <Card className="bg-light border-beige">
          <CardContent className="pt-4">
            <div className="flex items-end gap-3">
              <div className="flex-1 max-w-xs">
                <label className="text-xs text-grayish">Ticker</label>
                <Input
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase())}
                  onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
                  className="h-9"
                  placeholder="e.g. AAPL"
                />
              </div>
              <Button onClick={handleAnalyze} disabled={isLoading} className="bg-dark text-white hover:bg-dark/90 h-9">
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Calculator className="w-4 h-4" />}
                Analyze
              </Button>
            </div>
          </CardContent>
        </Card>

        {error && (
          <Alert className="border-accent-red bg-red-50">
            <AlertCircle className="h-4 w-4 text-accent-red" />
            <AlertDescription className="text-dark">{error}</AlertDescription>
          </Alert>
        )}

        {valuation && rating && (
          <>
            <Card className="bg-light border-beige">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <div>
                    <CardTitle className="text-xl font-bold text-dark">
                      {valuation.company_name} (${valuation.ticker})
                    </CardTitle>
                    <CardDescription className="text-xs text-grayish">
                      {valuation.sector} {valuation.industry ? `· ${valuation.industry}` : ""} · Current price ${valuation.current_price}
                    </CardDescription>
                  </div>
                  <Badge className={`${rating.color} text-white`}>{rating.label}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-6">
                  <div>
                    <p className="text-xs text-grayish">Blended fair value ({valuation.methods_applicable}/5 methods)</p>
                    <p className="text-3xl font-bold text-dark">
                      {valuation.blended_fair_value_per_share !== null ? `$${valuation.blended_fair_value_per_share}` : "N/A"}
                    </p>
                  </div>
                  {valuation.blended_upside_pct !== null && (
                    <div className="flex items-center gap-1">
                      {valuation.blended_upside_pct >= 0 ? (
                        <TrendingUp className="w-5 h-5 text-green-600" />
                      ) : (
                        <TrendingDown className="w-5 h-5 text-accent-red" />
                      )}
                      <span className={`text-lg font-semibold ${valuation.blended_upside_pct >= 0 ? "text-green-600" : "text-accent-red"}`}>
                        {valuation.blended_upside_pct >= 0 ? "+" : ""}{valuation.blended_upside_pct}%
                      </span>
                    </div>
                  )}
                </div>
                <p className="text-[11px] text-grayish mt-3 pt-3 border-t border-beige">{valuation.disclaimer}</p>
              </CardContent>
            </Card>

            {fairValueChartData.length > 1 && (
              <Card className="bg-light border-beige">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base font-semibold text-dark">Fair Value by Method</CardTitle>
                  <CardDescription className="text-xs text-grayish">
                    Current market price vs. each method&apos;s implied fair value per share
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={fairValueChartData} margin={{ top: 5, right: 10, left: 0, bottom: 40 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e1e0d9" vertical={false} />
                        <XAxis
                          dataKey="name"
                          tick={{ fontSize: 10, fill: "#8a8580" }}
                          angle={-25}
                          textAnchor="end"
                          interval={0}
                        />
                        <YAxis tick={{ fontSize: 10, fill: "#8a8580" }} tickFormatter={(v) => `$${v}`} width={45} />
                        <Tooltip formatter={(v: number) => [`$${v.toFixed(2)}`, "Fair value"]} />
                        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                          {fairValueChartData.map((entry, i) => (
                            <Cell key={i} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {valuation.methods.map((m) => (
                <MethodCard key={m.method} method={m} />
              ))}
            </div>

            <Card className="bg-light border-beige">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-accent-red" />
                  <div>
                    <CardTitle className="text-base font-semibold text-dark">Peer Performance Model</CardTitle>
                    <CardDescription className="text-xs text-grayish">
                      Logistic regression: fundamentals + sentiment + congressional trading signal vs. sector peers,
                      labeled by trailing return
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {!peerPerformance ? (
                  <>
                    <p className="text-xs text-grayish mb-3">
                      Fits a logistic regression on ~10-15 current sector peers (fundamentals, news sentiment, and
                      congressional trading signal as features; whether each peer beat the sector&apos;s trailing
                      return as the label), then scores {valuation.ticker} out-of-sample. This is a cross-sectional
                      snapshot, not a historical panel - see the methodology note once loaded.
                    </p>
                    <Button onClick={handleRunPeerPerformance} disabled={isLoadingPeers} className="bg-dark text-white hover:bg-dark/90">
                      {isLoadingPeers ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
                      Run Peer Performance Analysis
                    </Button>
                    {peerError && <p className="text-xs text-accent-red mt-2">{peerError}</p>}
                  </>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="p-3 bg-white rounded border border-beige text-center">
                        <p className="text-[11px] text-grayish">Outperformance probability</p>
                        <p className="text-lg font-bold text-dark">
                          {(peerPerformance.target.predicted_probability_of_outperformance * 100).toFixed(0)}%
                        </p>
                      </div>
                      <div className="p-3 bg-white rounded border border-beige text-center">
                        <p className="text-[11px] text-grayish">{valuation.ticker} trailing return</p>
                        <p className="text-lg font-bold text-dark">
                          {peerPerformance.target.trailing_return_pct !== null ? `${peerPerformance.target.trailing_return_pct}%` : "N/A"}
                        </p>
                      </div>
                      <div className="p-3 bg-white rounded border border-beige text-center">
                        <p className="text-[11px] text-grayish">Sector median return</p>
                        <p className="text-lg font-bold text-dark">{peerPerformance.sector_median_return_pct}%</p>
                      </div>
                      <div className="p-3 bg-white rounded border border-beige text-center">
                        <p className="text-[11px] text-grayish">Peers analyzed</p>
                        <p className="text-lg font-bold text-dark">{peerPerformance.peer_count}</p>
                      </div>
                    </div>

                    <div>
                      <p className="text-xs font-semibold text-dark mb-2">Feature correlation with outperformance</p>
                      <div className="h-56">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={coefficientChartData} layout="vertical" margin={{ left: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e1e0d9" horizontal={false} />
                            <XAxis type="number" tick={{ fontSize: 10 }} />
                            <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={140} />
                            <Tooltip />
                            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                              {coefficientChartData.map((entry, i) => (
                                <Cell key={i} fill={entry.value >= 0 ? "#0ca30c" : "#d03b3b"} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    <div>
                      <p className="text-xs font-semibold text-dark mb-2">Sector peers by trailing return</p>
                      <div className="max-h-56 overflow-y-auto space-y-1">
                        {peerPerformance.peer_table.map((p) => (
                          <div key={p.ticker} className="flex items-center justify-between p-2 bg-white rounded border border-beige text-xs">
                            <span className="text-dark font-medium">{p.ticker}</span>
                            <div className="flex items-center gap-2">
                              <span className={p.trailing_return_pct >= 0 ? "text-green-600" : "text-accent-red"}>
                                {p.trailing_return_pct >= 0 ? "+" : ""}{p.trailing_return_pct}%
                              </span>
                              {p.outperformed_median ? (
                                <TrendingUp className="w-3 h-3 text-green-600" />
                              ) : (
                                <Minus className="w-3 h-3 text-grayish" />
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <p className="text-[11px] text-grayish pt-3 border-t border-beige">{peerPerformance.methodology_caveat}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}

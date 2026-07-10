"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { LineChart as LineChartIcon, Loader2, TrendingDown, TrendingUp } from "lucide-react";
import { fetchPriceHistory, PriceHistoryResponse, PriceHistoryPeriod } from "@/lib/api";

interface PriceHistoryChartProps {
  ticker: string;
}

const PERIODS: { value: PriceHistoryPeriod; label: string }[] = [
  { value: "1mo", label: "1M" },
  { value: "3mo", label: "3M" },
  { value: "6mo", label: "6M" },
  { value: "1y", label: "1Y" },
  { value: "2y", label: "2Y" },
  { value: "5y", label: "5Y" },
];

function formatDate(dateStr: string, period: PriceHistoryPeriod): string {
  const d = new Date(dateStr);
  if (period === "1mo" || period === "3mo" || period === "6mo") {
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }
  return d.toLocaleDateString(undefined, { month: "short", year: "2-digit" });
}

interface TooltipPayloadItem {
  dataKey: string;
  value: number;
  color: string;
}

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipPayloadItem[]; label?: string }) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="bg-dark text-white text-xs rounded px-3 py-2 shadow-lg border border-beige/20">
      <p className="font-semibold mb-1">{label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} style={{ color: entry.color }}>
          {entry.dataKey === "close" ? "Close" : entry.dataKey.toUpperCase()}: ${entry.value?.toFixed(2)}
        </p>
      ))}
    </div>
  );
}

export default function PriceHistoryChart({ ticker }: PriceHistoryChartProps) {
  const [period, setPeriod] = useState<PriceHistoryPeriod>("6mo");
  const [data, setData] = useState<PriceHistoryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    fetchPriceHistory(ticker, period)
      .then((result) => {
        if (cancelled) return;
        if (result.success) {
          setData(result);
        } else {
          setData(null);
          setError(result.error || "Price history unavailable.");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData(null);
          setError("Failed to load price history. Yahoo Finance may be temporarily rate limited - try again shortly.");
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [ticker, period]);

  const isPositive = (data?.period_return_pct ?? 0) >= 0;
  const chartData = data?.points.map((p) => ({ ...p, label: formatDate(p.date, period) })) ?? [];

  return (
    <Card className="bg-light border-beige">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <LineChartIcon className="w-4 h-4 text-accent-red" />
            <div>
              <CardTitle className="text-base font-semibold text-dark">Price History</CardTitle>
              <CardDescription className="text-xs text-grayish">
                Close price with 20/50-day moving averages
              </CardDescription>
            </div>
          </div>
          <div className="flex gap-1 bg-white border border-beige rounded-md p-0.5">
            {PERIODS.map((p) => (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                  period === p.value
                    ? "bg-dark text-white"
                    : "text-grayish hover:text-dark"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="h-64 flex items-center justify-center">
            <Loader2 className="w-5 h-5 animate-spin text-grayish" />
          </div>
        )}

        {!isLoading && error && (
          <div className="h-64 flex items-center justify-center">
            <p className="text-xs text-grayish text-center max-w-sm">{error}</p>
          </div>
        )}

        {!isLoading && !error && data && (
          <>
            <div className="grid grid-cols-3 gap-2 mb-4">
              <div className="p-2.5 bg-white rounded border border-beige text-center">
                <p className="text-[10px] text-grayish">Period Return</p>
                <p className={`text-sm font-bold flex items-center justify-center gap-1 ${isPositive ? "text-green-600" : "text-accent-red"}`}>
                  {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                  {isPositive ? "+" : ""}{data.period_return_pct}%
                </p>
              </div>
              <div className="p-2.5 bg-white rounded border border-beige text-center">
                <p className="text-[10px] text-grayish">Period High</p>
                <p className="text-sm font-bold text-dark">{data.period_high !== null ? `$${data.period_high}` : "N/A"}</p>
              </div>
              <div className="p-2.5 bg-white rounded border border-beige text-center">
                <p className="text-[10px] text-grayish">Period Low</p>
                <p className="text-sm font-bold text-dark">{data.period_low !== null ? `$${data.period_low}` : "N/A"}</p>
              </div>
            </div>

            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="closeFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#eb5e28" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#eb5e28" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5dcd0" vertical={false} />
                  <XAxis
                    dataKey="label"
                    tick={{ fontSize: 10, fill: "#8a8580" }}
                    tickLine={false}
                    axisLine={{ stroke: "#e5dcd0" }}
                    minTickGap={40}
                  />
                  <YAxis
                    domain={["auto", "auto"]}
                    tick={{ fontSize: 10, fill: "#8a8580" }}
                    tickLine={false}
                    axisLine={false}
                    width={50}
                    tickFormatter={(v) => `$${v}`}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Area type="monotone" dataKey="close" stroke="#eb5e28" strokeWidth={2} fill="url(#closeFill)" dot={false} />
                  <Line type="monotone" dataKey="sma_20" stroke="#2f6690" strokeWidth={1.25} dot={false} strokeDasharray="4 2" />
                  <Line type="monotone" dataKey="sma_50" stroke="#8a8580" strokeWidth={1.25} dot={false} strokeDasharray="4 2" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex items-center gap-4 mt-2 text-[10px] text-grayish">
              <span className="flex items-center gap-1"><span className="w-2.5 h-0.5 bg-accent-red inline-block" /> Close</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-0.5 bg-[#2f6690] inline-block" /> 20-day SMA</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-0.5 bg-grayish inline-block" /> 50-day SMA</span>
              <span className="ml-auto">{data.source}</span>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FundamentalsResponse } from "@/lib/api";
import { BarChart3 } from "lucide-react";

interface FundamentalsPanelProps {
  fundamentals: FundamentalsResponse;
}

const RATING_COLORS: Record<string, string> = {
  strong: "bg-green-500",
  good: "bg-green-400",
  fair: "bg-yellow-400",
  weak: "bg-accent",
  insufficient_data: "bg-beige",
};

const METRIC_FORMAT: Record<string, (v: number) => string> = {
  pe_ratio: (v) => v.toFixed(1),
  peg_ratio: (v) => v.toFixed(2),
  price_to_book: (v) => v.toFixed(1),
  debt_to_equity: (v) => v.toFixed(2),
  current_ratio: (v) => v.toFixed(2),
  return_on_equity: (v) => `${(v * 100).toFixed(1)}%`,
  profit_margin: (v) => `${(v * 100).toFixed(1)}%`,
  revenue_growth: (v) => `${(v * 100).toFixed(1)}%`,
  earnings_growth: (v) => `${(v * 100).toFixed(1)}%`,
};

const METRIC_LABELS: Record<string, string> = {
  pe_ratio: "P/E Ratio",
  peg_ratio: "PEG Ratio",
  price_to_book: "Price/Book",
  debt_to_equity: "Debt/Equity",
  current_ratio: "Current Ratio",
  return_on_equity: "Return on Equity",
  profit_margin: "Profit Margin",
  revenue_growth: "Revenue Growth",
  earnings_growth: "Earnings Growth",
};

export default function FundamentalsPanel({ fundamentals }: FundamentalsPanelProps) {
  if (!fundamentals?.success) {
    return null;
  }

  const scoring = fundamentals.scoring;

  return (
    <Card className="bg-light border-beige">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-accent" />
            <div>
              <CardTitle className="text-base font-semibold text-dark">Fundamental Analysis</CardTitle>
              <CardDescription className="text-xs text-grayish">
                {fundamentals.sector} {fundamentals.industry ? `· ${fundamentals.industry}` : ""}
              </CardDescription>
            </div>
          </div>
          {scoring && (
            <div className="flex items-center gap-2">
              <Badge className={`${RATING_COLORS[scoring.rating] || "bg-beige"} text-white`}>
                {scoring.rating.replace("_", " ")}
              </Badge>
              <span className="text-lg font-bold text-dark">
                {scoring.overall_score !== null ? scoring.overall_score : "N/A"}
                <span className="text-xs text-grayish font-normal">/100</span>
              </span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {scoring?.breakdown.map((item) => (
            <div key={item.metric} className="p-2 bg-white rounded border border-beige">
              <p className="text-[11px] text-grayish">{METRIC_LABELS[item.metric] || item.metric}</p>
              <p className="text-sm font-semibold text-dark">
                {item.value !== null
                  ? (METRIC_FORMAT[item.metric] ? METRIC_FORMAT[item.metric](item.value) : item.value)
                  : "N/A"}
              </p>
              {item.score !== null && (
                <div className="h-1 mt-1 rounded-full bg-beige/50 overflow-hidden">
                  <div
                    className={`h-full ${item.score >= 75 ? "bg-green-500" : item.score >= 50 ? "bg-yellow-400" : "bg-accent"}`}
                    style={{ width: `${item.score}%` }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
        {scoring && (
          <p className="text-[11px] text-grayish mt-3">
            Data coverage: {scoring.data_coverage} metrics available
          </p>
        )}
      </CardContent>
    </Card>
  );
}

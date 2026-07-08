"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from "recharts";
import { CompositeScoreData } from "@/lib/api";

interface CompositeScoreGaugeProps {
  composite: CompositeScoreData;
}

const RATING_STYLES: Record<string, { color: string; label: string }> = {
  strongly_bullish: { color: "#22c55e", label: "Strongly Bullish" },
  bullish: { color: "#4ade80", label: "Bullish" },
  neutral: { color: "#eab308", label: "Neutral" },
  bearish: { color: "#f97316", label: "Bearish" },
  strongly_bearish: { color: "#eb5e28", label: "Strongly Bearish" },
  insufficient_data: { color: "#ccc5b9", label: "Insufficient Data" },
};

const COMPONENT_LABELS: Record<string, string> = {
  sentiment: "Sentiment",
  fundamentals: "Fundamentals",
  insider: "Political Insider",
  geopolitical: "Geopolitical",
  social_momentum: "Social Momentum",
};

export default function CompositeScoreGauge({ composite }: CompositeScoreGaugeProps) {
  const style = RATING_STYLES[composite.rating] || RATING_STYLES.insufficient_data;
  const score = composite.score ?? 0;

  const chartData = [{ name: "score", value: score, fill: style.color }];

  return (
    <Card className="bg-light border-beige">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base font-semibold text-dark">Sentilyze Score</CardTitle>
            <CardDescription className="text-xs text-grayish">
              Weighted composite across all signals
            </CardDescription>
          </div>
          <Badge style={{ backgroundColor: style.color }} className="text-white">
            {style.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col md:flex-row items-center gap-6">
          <div className="w-40 h-40 relative shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart
                innerRadius="70%"
                outerRadius="100%"
                data={chartData}
                startAngle={90}
                endAngle={-270}
              >
                <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
                <RadialBar background dataKey="value" cornerRadius={30} />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center flex-col">
              <span className="text-3xl font-bold text-dark">
                {composite.score !== null ? Math.round(composite.score) : "—"}
              </span>
              <span className="text-[10px] text-grayish">/ 100</span>
            </div>
          </div>

          <div className="flex-1 w-full space-y-2">
            {Object.entries(composite.components).map(([key, value]) => (
              <div key={key} className="flex items-center gap-3">
                <span className="text-xs text-grayish w-32 shrink-0">{COMPONENT_LABELS[key] || key}</span>
                <div className="flex-1 h-2 rounded-full bg-beige/50 overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${value ?? 0}%`,
                      backgroundColor: value === null ? "#ccc5b9" : style.color,
                    }}
                  />
                </div>
                <span className="text-xs font-medium text-dark w-10 text-right">
                  {value !== null ? Math.round(value) : "N/A"}
                </span>
              </div>
            ))}
          </div>
        </div>
        {composite.disclaimer && (
          <p className="text-[11px] text-grayish mt-4 pt-3 border-t border-beige">{composite.disclaimer}</p>
        )}
      </CardContent>
    </Card>
  );
}

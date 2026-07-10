"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SocialTrendsResponse } from "@/lib/api";
import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";
import { Flame } from "lucide-react";
import PanelIcon from "./PanelIcon";

interface SocialTrendsPanelProps {
  social: SocialTrendsResponse;
}

const MOMENTUM_STYLES: Record<string, string> = {
  surging: "bg-accent-red",
  rising: "bg-green-500",
  steady: "bg-yellow-400",
  fading: "bg-beige",
};

export default function SocialTrendsPanel({ social }: SocialTrendsPanelProps) {
  const momentum = social.reddit_momentum;
  const interest = social.search_interest;

  return (
    <Card className="bg-light border-beige">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <PanelIcon><Flame className="w-4 h-4" /></PanelIcon>
          <div>
            <CardTitle className="text-base font-semibold text-dark">Social & Search Momentum</CardTitle>
            <CardDescription className="text-xs text-grayish">Retail attention velocity</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {momentum?.success ? (
          <div className="flex items-center justify-between p-3 bg-white rounded border border-beige mb-3">
            <div>
              <p className="text-xs text-grayish">Reddit mentions today</p>
              <p className="text-xl font-bold text-dark">{momentum.mentions_today}</p>
              <p className="text-[11px] text-grayish">
                vs {momentum.trailing_week_daily_avg} / day trailing week avg
              </p>
            </div>
            {momentum.momentum && (
              <Badge className={`${MOMENTUM_STYLES[momentum.momentum]} text-white`}>{momentum.momentum}</Badge>
            )}
          </div>
        ) : (
          <p className="text-xs text-grayish mb-3">Reddit momentum data unavailable.</p>
        )}

        {interest?.success && interest.series && interest.series.length > 0 ? (
          <div>
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs text-grayish">Google Trends interest (90d)</p>
              {interest.trend_direction && (
                <span className="text-[11px] font-medium text-dark capitalize">{interest.trend_direction}</span>
              )}
            </div>
            <div className="h-16">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={interest.series}>
                  <YAxis domain={[0, 100]} hide />
                  <Line type="monotone" dataKey="interest" stroke="#eb5e28" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        ) : (
          <p className="text-xs text-grayish">
            {interest?.error || interest?.note || "Google Trends data unavailable."}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

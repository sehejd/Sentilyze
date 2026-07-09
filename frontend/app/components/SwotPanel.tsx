"use client";

import { ReactNode } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { SwotResponse } from "@/lib/api";
import { TrendingUp, TrendingDown, Target, ShieldAlert } from "lucide-react";

interface SwotPanelProps {
  swot: SwotResponse;
}

const QUADRANTS: Array<{
  key: keyof SwotResponse["swot"];
  title: string;
  icon: ReactNode;
  border: string;
  bg: string;
}> = [
  { key: "strengths", title: "Strengths", icon: <TrendingUp className="w-4 h-4 text-green-600" />, border: "border-green-200", bg: "bg-green-50" },
  { key: "weaknesses", title: "Weaknesses", icon: <TrendingDown className="w-4 h-4 text-accent-red" />, border: "border-red-200", bg: "bg-red-50" },
  { key: "opportunities", title: "Opportunities", icon: <Target className="w-4 h-4 text-blue-600" />, border: "border-blue-200", bg: "bg-blue-50" },
  { key: "threats", title: "Threats", icon: <ShieldAlert className="w-4 h-4 text-orange-600" />, border: "border-orange-200", bg: "bg-orange-50" },
];

export default function SwotPanel({ swot }: SwotPanelProps) {
  return (
    <Card className="bg-light border-beige">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold text-dark">SWOT Analysis</CardTitle>
        <CardDescription className="text-xs text-grayish">
          Strengths/weaknesses from fundamentals; opportunities/threats from sentiment, insider activity, geopolitics & social momentum
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {QUADRANTS.map((quadrant) => (
            <div key={quadrant.key} className={`p-3 rounded border ${quadrant.border} ${quadrant.bg}`}>
              <div className="flex items-center gap-2 mb-2">
                {quadrant.icon}
                <h4 className="text-sm font-semibold text-dark">{quadrant.title}</h4>
              </div>
              <ul className="space-y-1.5">
                {swot.swot[quadrant.key].map((bullet, i) => (
                  <li key={i} className="text-xs text-grayish leading-relaxed flex gap-1.5">
                    <span className="text-dark">•</span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        {swot.ai_narrative && (
          <div className="mt-3 pt-3 border-t border-beige">
            <p className="text-xs text-grayish leading-relaxed italic">{swot.ai_narrative}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

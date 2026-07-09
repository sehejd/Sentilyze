"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GeopoliticalResponse } from "@/lib/api";
import { Globe2, ExternalLink } from "lucide-react";

interface GeopoliticalPanelProps {
  geopolitical: GeopoliticalResponse;
}

const EXPOSURE_STYLES: Record<string, string> = {
  low: "bg-green-500",
  moderate: "bg-yellow-400",
  high: "bg-accent-red",
};

const THEME_LABELS: Record<string, string> = {
  trade_policy: "Trade Policy",
  sanctions: "Sanctions",
  conflict: "Conflict",
  elections_policy: "Elections & Regulation",
  monetary_policy: "Monetary Policy",
  supply_chain: "Supply Chain",
};

export default function GeopoliticalPanel({ geopolitical }: GeopoliticalPanelProps) {
  if (!geopolitical?.success) return null;

  const themeEntries = Object.entries(geopolitical.themes);

  return (
    <Card className="bg-light border-beige">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Globe2 className="w-4 h-4 text-accent-red" />
            <div>
              <CardTitle className="text-base font-semibold text-dark">Geopolitical Exposure</CardTitle>
              <CardDescription className="text-xs text-grayish">
                {geopolitical.total_articles} articles across risk themes, last 30 days
              </CardDescription>
            </div>
          </div>
          <Badge className={`${EXPOSURE_STYLES[geopolitical.geopolitical_exposure]} text-white`}>
            {geopolitical.geopolitical_exposure} exposure
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {themeEntries.length > 0 ? (
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {themeEntries.map(([theme, articles]) => (
              <div key={theme}>
                <p className="text-xs font-semibold text-dark mb-1">
                  {THEME_LABELS[theme] || theme} <span className="text-grayish font-normal">({articles.length})</span>
                </p>
                <ul className="space-y-1">
                  {articles.slice(0, 3).map((article, i) => (
                    <li key={i}>
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-grayish hover:text-accent-red flex items-center gap-1 line-clamp-1"
                      >
                        <ExternalLink className="w-3 h-3 shrink-0" />
                        {article.title}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-grayish">No notable geopolitical coverage found in the last month.</p>
        )}
      </CardContent>
    </Card>
  );
}

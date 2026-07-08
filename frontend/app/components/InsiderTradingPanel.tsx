"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { InsiderTradingResponse } from "@/lib/api";
import { Landmark } from "lucide-react";

interface InsiderTradingPanelProps {
  insider: InsiderTradingResponse;
}

const SIGNAL_STYLES: Record<string, { label: string; color: string }> = {
  net_buying: { label: "Net Buying", color: "bg-green-500" },
  net_selling: { label: "Net Selling", color: "bg-accent" },
  mixed: { label: "Mixed Activity", color: "bg-yellow-400" },
  no_activity: { label: "No Recent Activity", color: "bg-beige" },
};

export default function InsiderTradingPanel({ insider }: InsiderTradingPanelProps) {
  if (!insider?.success) return null;

  const signal = SIGNAL_STYLES[insider.aggregate.signal_label] || SIGNAL_STYLES.no_activity;

  return (
    <Card className="bg-light border-beige">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Landmark className="w-4 h-4 text-accent" />
            <div>
              <CardTitle className="text-base font-semibold text-dark">Political Insider Trading</CardTitle>
              <CardDescription className="text-xs text-grayish">
                Congressional STOCK Act disclosures, last {insider.lookback_days} days
              </CardDescription>
            </div>
          </div>
          <Badge className={`${signal.color} text-white`}>{signal.label}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-3 mb-3">
          <div className="p-2 bg-white rounded border border-beige text-center">
            <p className="text-[11px] text-grayish">Transactions</p>
            <p className="text-lg font-bold text-dark">{insider.total_found}</p>
          </div>
          <div className="p-2 bg-white rounded border border-beige text-center">
            <p className="text-[11px] text-grayish">Members</p>
            <p className="text-lg font-bold text-dark">{insider.aggregate.unique_members}</p>
          </div>
          <div className="p-2 bg-white rounded border border-beige text-center">
            <p className="text-[11px] text-grayish">Net Signal</p>
            <p className="text-lg font-bold text-dark">{insider.aggregate.net_signal.toFixed(2)}</p>
          </div>
        </div>

        {insider.transactions.length > 0 ? (
          <div className="space-y-2 max-h-56 overflow-y-auto">
            {insider.transactions.slice(0, 8).map((tx, i) => (
              <div key={i} className="flex items-center justify-between p-2 bg-white rounded border border-beige text-xs">
                <div>
                  <p className="font-medium text-dark">{tx.member} <span className="text-grayish font-normal">({tx.chamber})</span></p>
                  <p className="text-grayish">{new Date(tx.transaction_date).toLocaleDateString()} · {tx.amount_range}</p>
                </div>
                <Badge
                  className={
                    tx.transaction_type.toLowerCase().includes("purchase")
                      ? "bg-green-500 text-white"
                      : "bg-accent text-white"
                  }
                >
                  {tx.transaction_type}
                </Badge>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-grayish">No disclosed congressional trades found in this window.</p>
        )}
      </CardContent>
    </Card>
  );
}

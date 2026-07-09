"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Gavel, Users, Network, Loader2, ExternalLink, AlertTriangle } from "lucide-react";
import { fetchPoliticalNetwork, PoliticalNetworkResponse } from "@/lib/api";

interface PoliticalNetworkPanelProps {
  ticker: string;
  companyName: string;
}

function formatMoney(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) return "N/A";
  return `$${amount.toLocaleString()}`;
}

export default function PoliticalNetworkPanel({ ticker, companyName }: PoliticalNetworkPanelProps) {
  const [data, setData] = useState<PoliticalNetworkResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoad = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetchPoliticalNetwork(ticker, companyName);
      setData(result);
    } catch {
      setError("Failed to load the political network deep dive. This fans out to several slower public APIs (Senate LDA, Congress.gov, FEC) - try again in a moment.");
    } finally {
      setIsLoading(false);
    }
  };

  if (!data) {
    return (
      <Card className="bg-light border-beige">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Network className="w-4 h-4 text-accent-red" />
            <div>
              <CardTitle className="text-base font-semibold text-dark">Political Network - Deeper Dive</CardTitle>
              <CardDescription className="text-xs text-grayish">
                Lobbying, bills, sponsors, executives & campaign contributions
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-grayish mb-3">
            Cross-references what {companyName || ticker} lobbies for (Senate LDA filings), which bills and
            sponsors that involves (Congress.gov), who the company&apos;s executives are, and what politicians
            those executives personally donate to (FEC). This calls several slower public APIs, so it&apos;s
            loaded on demand.
          </p>
          <Button onClick={handleLoad} disabled={isLoading} className="bg-dark text-white hover:bg-dark/90">
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Network className="w-4 h-4" />}
            Load Deeper Dive
          </Button>
          {error && <p className="text-xs text-accent-red mt-2">{error}</p>}
        </CardContent>
      </Card>
    );
  }

  const hasLobbying = data.lobbying.success && data.lobbying.total_filings > 0;

  return (
    <Card className="bg-light border-beige">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-accent-red" />
          <div>
            <CardTitle className="text-base font-semibold text-dark">Political Network - Deeper Dive</CardTitle>
            <CardDescription className="text-xs text-grayish">{data.disclaimer}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Connections callouts */}
        {data.connections.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-dark flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-accent-red" />
              Possible Connections
            </h4>
            {data.connections.map((connection, i) => (
              <div key={i} className="p-2.5 bg-amber-50 border border-amber-200 rounded text-xs text-dark">
                {connection.description}
                <span className="block text-[10px] text-grayish mt-1">
                  Confidence: {connection.confidence.replace(/_/g, " ")} - verify manually
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Lobbying summary */}
        <div>
          <h4 className="text-sm font-semibold text-dark flex items-center gap-1.5 mb-2">
            <Gavel className="w-3.5 h-3.5" /> Lobbying Activity
          </h4>
          {hasLobbying ? (
            <>
              <div className="grid grid-cols-3 gap-2 mb-2">
                <div className="p-2 bg-white rounded border border-beige text-center">
                  <p className="text-[10px] text-grayish">Filings</p>
                  <p className="text-sm font-bold text-dark">{data.lobbying.total_filings}</p>
                </div>
                <div className="p-2 bg-white rounded border border-beige text-center">
                  <p className="text-[10px] text-grayish">Est. Spend</p>
                  <p className="text-sm font-bold text-dark">{formatMoney(data.lobbying.estimated_total_spend)}</p>
                </div>
                <div className="p-2 bg-white rounded border border-beige text-center">
                  <p className="text-[10px] text-grayish">Firms Retained</p>
                  <p className="text-sm font-bold text-dark">{data.lobbying.registrants.length}</p>
                </div>
              </div>
              {Object.keys(data.lobbying.issue_areas).length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(data.lobbying.issue_areas).map(([area, count]) => (
                    <Badge key={area} className="bg-beige text-dark font-normal">
                      {area} ({count})
                    </Badge>
                  ))}
                </div>
              )}
            </>
          ) : (
            <p className="text-xs text-grayish">
              {data.lobbying.success ? "No lobbying filings found for this company." : data.lobbying.error}
            </p>
          )}
        </div>

        {/* Bills */}
        {data.bills.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-dark mb-2">Bills Lobbied On</h4>
            {!data.congress_gov_configured && (
              <p className="text-[11px] text-grayish mb-2">
                Set CONGRESS_GOV_API_KEY in the backend .env for bill titles & sponsors (free signup).
              </p>
            )}
            <div className="space-y-2">
              {data.bills.map((bill, i) => (
                <div key={i} className="p-2.5 bg-white rounded border border-beige text-xs">
                  {bill.success ? (
                    <>
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <span className="font-semibold text-dark">
                          {bill.bill_type.toUpperCase()} {bill.bill_number}
                        </span>
                        {bill.congress_gov_url && (
                          <a href={bill.congress_gov_url} target="_blank" rel="noopener noreferrer" className="text-grayish hover:text-accent-red flex items-center gap-1">
                            <ExternalLink className="w-3 h-3" /> View
                          </a>
                        )}
                      </div>
                      <p className="text-dark mt-1">{bill.title}</p>
                      {bill.sponsor && (
                        <p className="text-grayish mt-1">
                          Sponsor: {bill.sponsor.name} ({bill.sponsor.party}-{bill.sponsor.state}) · {bill.cosponsors_count ?? 0} cosponsors
                        </p>
                      )}
                      {bill.mentions !== undefined && bill.mentions !== null && (
                        <p className="text-[10px] text-grayish mt-1">Mentioned in {bill.mentions} filing text(s)</p>
                      )}
                    </>
                  ) : (
                    <p className="text-grayish">
                      {bill.bill_type.toUpperCase()} {bill.bill_number} - {bill.error}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Executives & donations */}
        <div>
          <h4 className="text-sm font-semibold text-dark flex items-center gap-1.5 mb-2">
            <Users className="w-3.5 h-3.5" /> Executives & Political Contributions
          </h4>
          {data.executive_donations && data.executive_donations.executives.length > 0 ? (
            <div className="space-y-2">
              {data.executive_donations.executives.map((exec, i) => (
                <div key={i} className="p-2.5 bg-white rounded border border-beige text-xs">
                  <p className="font-semibold text-dark">{exec.name} <span className="text-grayish font-normal">({exec.title})</span></p>
                  {exec.donations.length > 0 ? (
                    <ul className="mt-1 space-y-1">
                      {exec.donations.map((donation, j) => (
                        <li key={j} className="text-grayish">
                          {formatMoney(donation.amount)} to {donation.candidate_name || donation.committee_name}
                          {donation.committee_party ? ` (${donation.committee_party})` : ""} on {donation.date}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-grayish mt-1">No FEC contribution records found under this employer.</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-grayish">No named officer data available for this ticker.</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

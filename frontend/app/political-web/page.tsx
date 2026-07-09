"use client";

import { useState, useRef, useMemo, useCallback, WheelEvent, MouseEvent } from "react";
import Link from "next/link";
import { ArrowLeft, Network, Loader2, AlertCircle, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { fetchPoliticalWeb, PoliticalWebResponse, PoliticalWebNodeType, PoliticalWebEdgeType } from "@/lib/api";
import { computeGraphLayout, LayoutNode, LayoutLink } from "@/lib/graphLayout";

const WIDTH = 1100;
const HEIGHT = 720;

// Categorical palette, validated for CVD separation (dataviz skill, fixed slot order)
const NODE_COLORS: Record<PoliticalWebNodeType, string> = {
  company: "#2a78d6", // blue
  politician: "#1baf7a", // aqua
  bill: "#eda100", // yellow
  executive: "#4a3aa7", // violet
};

const NODE_LABELS: Record<PoliticalWebNodeType, string> = {
  company: "Company",
  politician: "Politician",
  bill: "Bill",
  executive: "Executive",
};

const EDGE_LABELS: Record<PoliticalWebEdgeType, string> = {
  trades: "Discloses trading",
  lobbies_for: "Lobbies for",
  sponsored_by: "Sponsored by",
  works_at: "Works at",
  donated_to: "Donated to",
};

function edgeColor(link: LayoutLink): string {
  if (link.type === "trades") {
    if (link.direction === "net_buying") return "#0ca30c";
    if (link.direction === "net_selling") return "#d03b3b";
    return "#c3c2b7";
  }
  if (link.type === "donated_to") return "#eb6834";
  return "#c3c2b7";
}

function nodeRadius(node: LayoutNode): number {
  return 5 + Math.min(16, node.degree * 1.3);
}

export default function PoliticalWebPage() {
  const [daysBack, setDaysBack] = useState("730");
  const [maxTradingEdges, setMaxTradingEdges] = useState("80");
  const [maxLobbyingCompanies, setMaxLobbyingCompanies] = useState("12");
  const [maxDonationCompanies, setMaxDonationCompanies] = useState("0");

  const [data, setData] = useState<PoliticalWebResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [dragPositions, setDragPositions] = useState<Record<string, { x: number; y: number }>>({});
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [view, setView] = useState({ x: 0, y: 0, scale: 1 });

  const svgRef = useRef<SVGSVGElement>(null);
  const dragNodeId = useRef<string | null>(null);
  const panState = useRef<{ startX: number; startY: number; viewX: number; viewY: number } | null>(null);

  const layout = useMemo(() => {
    if (!data) return null;
    return computeGraphLayout(data.nodes, data.edges, WIDTH, HEIGHT);
  }, [data]);

  const nodesById = useMemo(() => {
    const map = new Map<string, LayoutNode>();
    layout?.nodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [layout]);

  const handleBuild = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setData(null);
    setSelectedId(null);
    setDragPositions({});
    try {
      const result = await fetchPoliticalWeb({
        days_back: parseInt(daysBack, 10) || 730,
        max_trading_edges: parseInt(maxTradingEdges, 10) || 80,
        max_lobbying_companies: parseInt(maxLobbyingCompanies, 10) || 0,
        max_donation_companies: parseInt(maxDonationCompanies, 10) || 0,
      });
      if (!result.success) {
        setError(result.error || "Failed to build the political web");
      } else {
        setData(result);
      }
    } catch {
      setError("Failed to build the political web. This can take a while with larger caps - try lowering them.");
    } finally {
      setIsLoading(false);
    }
  }, [daysBack, maxTradingEdges, maxLobbyingCompanies, maxDonationCompanies]);

  const getPos = useCallback(
    (id: string): { x: number; y: number } => {
      if (dragPositions[id]) return dragPositions[id];
      const n = nodesById.get(id);
      return { x: n?.x ?? 0, y: n?.y ?? 0 };
    },
    [dragPositions, nodesById]
  );

  const screenToSvg = useCallback((clientX: number, clientY: number) => {
    const svg = svgRef.current;
    if (!svg) return { x: 0, y: 0 };
    const rect = svg.getBoundingClientRect();
    const x = ((clientX - rect.left) / rect.width) * WIDTH;
    const y = ((clientY - rect.top) / rect.height) * HEIGHT;
    return { x: (x - view.x) / view.scale, y: (y - view.y) / view.scale };
  }, [view]);

  const handleNodeMouseDown = (id: string) => (e: MouseEvent) => {
    e.stopPropagation();
    dragNodeId.current = id;
  };

  const handleBackgroundMouseDown = (e: MouseEvent) => {
    panState.current = { startX: e.clientX, startY: e.clientY, viewX: view.x, viewY: view.y };
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (dragNodeId.current) {
      const pos = screenToSvg(e.clientX, e.clientY);
      setDragPositions((prev) => ({ ...prev, [dragNodeId.current as string]: pos }));
    } else if (panState.current) {
      const dx = e.clientX - panState.current.startX;
      const dy = e.clientY - panState.current.startY;
      setView((v) => ({ ...v, x: panState.current!.viewX + dx, y: panState.current!.viewY + dy }));
    }
  };

  const handleMouseUp = () => {
    dragNodeId.current = null;
    panState.current = null;
  };

  const handleWheel = (e: WheelEvent) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 0.9 : 1.1;
    setView((v) => ({ ...v, scale: Math.max(0.3, Math.min(3, v.scale * factor)) }));
  };

  const resetView = () => setView({ x: 0, y: 0, scale: 1 });

  const connectedIds = useMemo(() => {
    if (!hoveredId && !selectedId) return null;
    const focusId = selectedId || hoveredId;
    const ids = new Set<string>([focusId as string]);
    layout?.links.forEach((l) => {
      if (l.source.id === focusId) ids.add(l.target.id);
      if (l.target.id === focusId) ids.add(l.source.id);
    });
    return ids;
  }, [hoveredId, selectedId, layout]);

  const selectedNode = selectedId ? nodesById.get(selectedId) : null;
  const selectedConnections = useMemo(() => {
    if (!selectedId || !layout) return [];
    return layout.links
      .filter((l) => l.source.id === selectedId || l.target.id === selectedId)
      .map((l) => {
        const other = l.source.id === selectedId ? l.target : l.source;
        return { link: l, other };
      });
  }, [selectedId, layout]);

  return (
    <div className="min-h-screen bg-light px-6 py-10">
      <div className="max-w-7xl mx-auto space-y-4">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-grayish hover:text-dark">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-dark flex items-center gap-2">
              <Network className="w-7 h-7 text-accent-red" />
              Political Web
            </h1>
            <p className="text-sm text-grayish">
              Every disclosed politician↔company congressional trade, enriched with lobbying, bill sponsors,
              and executive donations for the most active companies.
            </p>
          </div>
        </div>

        <Card className="bg-light border-beige">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold text-dark">Graph Parameters</CardTitle>
            <CardDescription className="text-xs text-grayish">
              The trading layer covers the full public STOCK Act dataset. Lobbying/bill-sponsor and donation
              layers are capped per company since those hit slower public APIs (Senate LDA, Congress.gov, FEC) -
              larger caps take longer to build.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 items-end">
              <div>
                <label className="text-xs text-grayish">Days back</label>
                <Input type="number" value={daysBack} onChange={(e) => setDaysBack(e.target.value)} className="h-8 text-sm" />
              </div>
              <div>
                <label className="text-xs text-grayish">Max trading edges</label>
                <Input type="number" value={maxTradingEdges} onChange={(e) => setMaxTradingEdges(e.target.value)} className="h-8 text-sm" />
              </div>
              <div>
                <label className="text-xs text-grayish">Max companies (lobbying)</label>
                <Input type="number" value={maxLobbyingCompanies} onChange={(e) => setMaxLobbyingCompanies(e.target.value)} className="h-8 text-sm" />
              </div>
              <div>
                <label className="text-xs text-grayish">Max companies (donations)</label>
                <Input type="number" value={maxDonationCompanies} onChange={(e) => setMaxDonationCompanies(e.target.value)} className="h-8 text-sm" />
              </div>
              <Button onClick={handleBuild} disabled={isLoading} className="bg-dark text-white hover:bg-dark/90 h-8">
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Network className="w-4 h-4" />}
                Build Graph
              </Button>
            </div>
            {isLoading && (
              <p className="text-xs text-grayish mt-2">
                Building - this fans out across several public APIs and can take 30s-2min depending on caps.
              </p>
            )}
          </CardContent>
        </Card>

        {error && (
          <Alert className="border-accent-red bg-red-50">
            <AlertCircle className="h-4 w-4 text-accent-red" />
            <AlertDescription className="text-dark">{error}</AlertDescription>
          </Alert>
        )}

        {data && layout && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="p-3 bg-white rounded border border-beige text-center">
                <p className="text-[11px] text-grayish">Nodes shown</p>
                <p className="text-lg font-bold text-dark">{data.stats.total_nodes}</p>
              </div>
              <div className="p-3 bg-white rounded border border-beige text-center">
                <p className="text-[11px] text-grayish">Edges shown</p>
                <p className="text-lg font-bold text-dark">{data.stats.total_edges}</p>
              </div>
              <div className="p-3 bg-white rounded border border-beige text-center">
                <p className="text-[11px] text-grayish">Total disclosed pairs</p>
                <p className="text-lg font-bold text-dark">{data.stats.total_disclosed_trading_pairs}</p>
              </div>
              <div className="p-3 bg-white rounded border border-beige text-center">
                <p className="text-[11px] text-grayish">Dataset transactions</p>
                <p className="text-lg font-bold text-dark">{data.stats.dataset_totals.total_transactions}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
              <Card className="bg-light border-beige lg:col-span-3">
                <CardContent className="p-0 relative">
                  <div className="absolute top-2 right-2 z-10 flex gap-1">
                    <button onClick={() => setView((v) => ({ ...v, scale: Math.min(3, v.scale * 1.2) }))} className="p-1.5 bg-white border border-beige rounded hover:bg-beige/30">
                      <ZoomIn className="w-3.5 h-3.5 text-dark" />
                    </button>
                    <button onClick={() => setView((v) => ({ ...v, scale: Math.max(0.3, v.scale * 0.8) }))} className="p-1.5 bg-white border border-beige rounded hover:bg-beige/30">
                      <ZoomOut className="w-3.5 h-3.5 text-dark" />
                    </button>
                    <button onClick={resetView} className="p-1.5 bg-white border border-beige rounded hover:bg-beige/30">
                      <Maximize2 className="w-3.5 h-3.5 text-dark" />
                    </button>
                  </div>
                  <svg
                    ref={svgRef}
                    viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
                    width="100%"
                    height={HEIGHT}
                    className="bg-white rounded cursor-grab active:cursor-grabbing"
                    onMouseDown={handleBackgroundMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                    onWheel={handleWheel}
                    onClick={() => setSelectedId(null)}
                  >
                    <g transform={`translate(${view.x},${view.y}) scale(${view.scale})`}>
                      {layout.links.map((link, i) => {
                        const source = getPos(link.source.id);
                        const target = getPos(link.target.id);
                        const dimmed = connectedIds ? !(connectedIds.has(link.source.id) && connectedIds.has(link.target.id)) : false;
                        return (
                          <line
                            key={i}
                            x1={source.x}
                            y1={source.y}
                            x2={target.x}
                            y2={target.y}
                            stroke={edgeColor(link)}
                            strokeWidth={link.type === "donated_to" ? 2 : 1}
                            opacity={dimmed ? 0.08 : link.type === "trades" ? 0.35 : 0.55}
                          />
                        );
                      })}
                      {layout.nodes.map((node) => {
                        const pos = getPos(node.id);
                        const dimmed = connectedIds ? !connectedIds.has(node.id) : false;
                        const isFocused = node.id === selectedId || node.id === hoveredId;
                        return (
                          <g
                            key={node.id}
                            transform={`translate(${pos.x},${pos.y})`}
                            onMouseDown={handleNodeMouseDown(node.id)}
                            onMouseEnter={() => setHoveredId(node.id)}
                            onMouseLeave={() => setHoveredId(null)}
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedId(node.id === selectedId ? null : node.id);
                            }}
                            style={{ cursor: "pointer" }}
                            opacity={dimmed ? 0.15 : 1}
                          >
                            <circle
                              r={nodeRadius(node)}
                              fill={NODE_COLORS[node.type]}
                              stroke={isFocused ? "#252422" : "white"}
                              strokeWidth={isFocused ? 2 : 1.5}
                            />
                            {(isFocused || node.degree >= 4) && (
                              <text
                                x={nodeRadius(node) + 4}
                                y={4}
                                fontSize={11}
                                fill="#252422"
                                style={{ pointerEvents: "none" }}
                              >
                                {node.label}
                              </text>
                            )}
                          </g>
                        );
                      })}
                    </g>
                  </svg>
                </CardContent>
              </Card>

              <div className="space-y-4">
                <Card className="bg-light border-beige">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-semibold text-dark">Legend</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <p className="text-[11px] text-grayish mb-1.5">Node type</p>
                      <div className="space-y-1">
                        {(Object.keys(NODE_COLORS) as PoliticalWebNodeType[]).map((t) => (
                          <div key={t} className="flex items-center gap-2 text-xs text-dark">
                            <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: NODE_COLORS[t] }} />
                            {NODE_LABELS[t]}
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-[11px] text-grayish mb-1.5">Edge type</p>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 text-xs text-dark">
                          <span className="w-3 h-0.5 inline-block bg-[#0ca30c]" /> Trades (net buying)
                        </div>
                        <div className="flex items-center gap-2 text-xs text-dark">
                          <span className="w-3 h-0.5 inline-block bg-[#d03b3b]" /> Trades (net selling)
                        </div>
                        <div className="flex items-center gap-2 text-xs text-dark">
                          <span className="w-3 h-0.5 inline-block bg-[#eb6834]" /> Donated to
                        </div>
                        <div className="flex items-center gap-2 text-xs text-dark">
                          <span className="w-3 h-0.5 inline-block bg-[#c3c2b7]" /> Lobbies / sponsors / works at
                        </div>
                      </div>
                    </div>
                    <p className="text-[10px] text-grayish pt-2 border-t border-beige">
                      Drag nodes to rearrange. Scroll to zoom, drag background to pan. Click a node for details.
                    </p>
                  </CardContent>
                </Card>

                <Card className="bg-light border-beige">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-semibold text-dark">
                      {selectedNode ? selectedNode.label : "Node details"}
                    </CardTitle>
                    {selectedNode && (
                      <CardDescription className="text-xs text-grayish">
                        {NODE_LABELS[selectedNode.type]}
                        {selectedNode.party ? ` · ${selectedNode.party}${selectedNode.state ? "-" + selectedNode.state : ""}` : ""}
                        {selectedNode.title ? ` · ${selectedNode.title}` : ""}
                      </CardDescription>
                    )}
                  </CardHeader>
                  <CardContent>
                    {selectedNode ? (
                      <div className="space-y-1.5 max-h-64 overflow-y-auto">
                        {selectedConnections.map(({ link, other }, i) => (
                          <div key={i} className="text-xs text-dark p-1.5 bg-white rounded border border-beige">
                            <span className="text-grayish">{EDGE_LABELS[link.type]}</span> {other.label}
                            {link.type === "trades" && link.direction && (
                              <span className="text-grayish"> ({link.direction.replace("_", " ")}, {link.weight}x)</span>
                            )}
                            {link.type === "donated_to" && link.amount && (
                              <span className="text-grayish"> (${link.amount.toLocaleString()})</span>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-grayish">Click a node in the graph to see its connections.</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>

            <p className="text-[11px] text-grayish">{data.disclaimer}</p>
          </>
        )}
      </div>
    </div>
  );
}

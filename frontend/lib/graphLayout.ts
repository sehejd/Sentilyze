import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide, SimulationNodeDatum } from "d3-force";
import { PoliticalWebNode, PoliticalWebEdge } from "@/lib/api";

export interface LayoutNode extends SimulationNodeDatum, PoliticalWebNode {
  degree: number;
}

export interface LayoutLink {
  source: LayoutNode;
  target: LayoutNode;
  type: PoliticalWebEdge["type"];
  weight: number;
  direction?: PoliticalWebEdge["direction"];
  amount?: number;
  date?: string;
}

/**
 * Runs a static (non-animated) force simulation - ticks synchronously to a
 * stable layout rather than driving a live physics loop, which keeps this
 * simple and cheap to render even for a few hundred nodes.
 */
export function computeGraphLayout(
  nodes: PoliticalWebNode[],
  edges: PoliticalWebEdge[],
  width: number,
  height: number
): { nodes: LayoutNode[]; links: LayoutLink[] } {
  const degree = new Map<string, number>();
  for (const edge of edges) {
    degree.set(edge.source, (degree.get(edge.source) || 0) + 1);
    degree.set(edge.target, (degree.get(edge.target) || 0) + 1);
  }

  const layoutNodes: LayoutNode[] = nodes.map((n) => ({
    ...n,
    degree: degree.get(n.id) || 0,
  }));

  const simulation = forceSimulation(layoutNodes)
    .force(
      "link",
      forceLink<LayoutNode, PoliticalWebEdge & { source: string; target: string }>(edges as never)
        .id((d) => (d as unknown as LayoutNode).id)
        .distance((l) => (((l as unknown as { type: string }).type === "trades") ? 90 : 60))
        .strength(0.25)
    )
    .force("charge", forceManyBody().strength(-140))
    .force("center", forceCenter(width / 2, height / 2))
    .force(
      "collide",
      forceCollide<LayoutNode>().radius((d) => 14 + Math.min(20, d.degree * 1.5))
    )
    .stop();

  const tickCount = Math.min(400, Math.max(120, layoutNodes.length * 2));
  for (let i = 0; i < tickCount; i++) simulation.tick();

  const links = simulation.force<ReturnType<typeof forceLink>>("link")!.links() as unknown as LayoutLink[];

  return { nodes: layoutNodes, links };
}

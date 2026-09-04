import {useMemo, useState} from 'react';

import Link from '@docusaurus/Link';
import {usePluginData} from '@docusaurus/useGlobalData';

import type {FeatureGraph as FeatureGraphDocument} from '../../plugins/concorde-content/types';
import FeatureGraph from './FeatureGraph';

interface GlobalData {featureGraph: FeatureGraphDocument}

/**
 * `entity.auto-docs.neighborhood-view`: the depth-one neighborhood of one feature — itself plus every
 * feature reachable by exactly one typed or interface-derived edge — rendered with the same
 * `FeatureGraph` renderer as `/graph`, filtered to just that neighborhood (FR-008).
 */
export default function FeatureNeighborhood({featureId}: {featureId: string}) {
  const data = usePluginData('concorde-content') as unknown as GlobalData;
  const graph = data.featureGraph;
  const [selectedId, setSelectedId] = useState<string | undefined>(featureId);

  const neighborhood = useMemo(() => {
    const neighborEdges = graph.edges.filter((edge) => edge.source === featureId || edge.target === featureId);
    const featureIds = new Set<string>([featureId, ...neighborEdges.flatMap((edge) => [edge.source, edge.target])]);
    const features = graph.features.filter((feature) => featureIds.has(feature.id));
    const moduleIds = new Set(features.map((feature) => feature.module));
    const modules = graph.modules.filter((module) => moduleIds.has(module.id));
    return {modules, features, edges: neighborEdges};
  }, [graph, featureId]);

  if (!neighborhood.features.some((feature) => feature.id === featureId)) return null;

  return (
    <section className="featureNeighborhood" aria-labelledby="feature-neighborhood-heading">
      <div className="architectureView__heading">
        <div>
          <p className="architectureView__eyebrow">Feature graph</p>
          <h2 id="feature-neighborhood-heading">Neighborhood</h2>
        </div>
        <Link to="/graph">Open the full graph</Link>
      </div>
      {neighborhood.edges.length === 0 && (
        <p className="featureNeighborhood__empty">This feature declares no typed relations or interface dependencies yet.</p>
      )}
      <FeatureGraph
        modules={neighborhood.modules}
        features={neighborhood.features}
        edges={neighborhood.edges}
        selectedFeatureId={selectedId}
        onSelect={setSelectedId}
        height="32rem"
        minZoomAfterFit={1}
      />
    </section>
  );
}

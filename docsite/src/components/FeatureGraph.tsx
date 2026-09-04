import type cytoscape from 'cytoscape';
import {useEffect, useRef} from 'react';

import BrowserOnly from '@docusaurus/BrowserOnly';

import type {EdgeKind, GraphEdge, GraphFeature, GraphModule} from '../../plugins/concorde-content/types';

export interface FeatureGraphProps {
  modules: GraphModule[];
  features: GraphFeature[];
  edges: GraphEdge[];
  /** The currently selected feature; its closed neighborhood is highlighted and everything else dims. */
  selectedFeatureId?: string;
  /** Fires with the tapped feature's ID, or `undefined` when the background is tapped to deselect. */
  onSelect?: (featureId: string | undefined) => void;
  height?: string;
  /**
   * Zoom floor enforced right after the initial fit-to-viewport, so a small graph is not shrunk into
   * illegibility: a depth-one neighborhood wants ~1 (its handful of nodes should render at native
   * size), the global `/graph` view wants a lower floor like 0.6 so a larger graph still fits.
   */
  minZoomAfterFit?: number;
}

interface GraphColors {
  moduleBackground: string;
  moduleBorder: string;
  moduleText: string;
  featureBackground: string;
  featureText: string;
  featureBorder: string;
  selected: string;
  edge: Record<EdgeKind, string>;
}

const EDGE_KINDS: EdgeKind[] = ['composes', 'refines', 'depends_on', 'relates_to', 'requires'];

/** Reads the theme-aware palette from `src/css/custom.css` custom properties, resolved for the current theme. */
function readGraphColors(): GraphColors {
  const style = getComputedStyle(document.documentElement);
  const read = (name: string, fallback: string) => style.getPropertyValue(name).trim() || fallback;
  return {
    moduleBackground: read('--graph-module-bg', '#eef0fd'),
    moduleBorder: read('--graph-module-border', '#c7cbf0'),
    moduleText: read('--graph-module-text', '#2b2f57'),
    featureBackground: read('--graph-feature-bg', '#3f4fd7'),
    featureText: read('--graph-feature-text', '#ffffff'),
    featureBorder: read('--graph-feature-border', '#232f99'),
    selected: read('--graph-selected', '#ff8a00'),
    edge: {
      composes: read('--graph-edge-composes', '#3f4fd7'),
      refines: read('--graph-edge-refines', '#00897b'),
      depends_on: read('--graph-edge-depends-on', '#c2410c'),
      relates_to: read('--graph-edge-relates-to', '#9aa0b4'),
      requires: read('--graph-edge-requires', '#b3245c'),
    },
  };
}

function toElements(modules: GraphModule[], features: GraphFeature[], edges: GraphEdge[]): cytoscape.ElementDefinition[] {
  const moduleIds = new Set(modules.map((module) => module.id));
  const featureIds = new Set(features.map((feature) => feature.id));
  return [
    ...modules.map((module): cytoscape.ElementDefinition => ({
      data: {
        id: module.id, label: module.title, kind: 'module',
        ...(module.parent && moduleIds.has(module.parent) ? {parent: module.parent} : {}),
      },
    })),
    ...features.map((feature): cytoscape.ElementDefinition => ({
      data: {
        id: feature.id, label: feature.title, kind: 'feature',
        ...(moduleIds.has(feature.module) ? {parent: feature.module} : {}),
      },
    })),
    ...edges
      .filter((edge) => featureIds.has(edge.source) && featureIds.has(edge.target))
      .map((edge): cytoscape.ElementDefinition => ({
        data: {
          id: edge.id, source: edge.source, target: edge.target, kind: edge.kind,
          label: edge.kind === 'requires' ? edge.interface ?? '' : '',
        },
      })),
  ];
}

/** Distinct per-kind styling (FR-007): color, arrowhead, and line dash pattern each say which relation an edge carries. */
function buildStylesheet(colors: GraphColors): cytoscape.StylesheetJson {
  const rules: Array<{selector: string; style: Record<string, unknown>}> = [
    {selector: 'node[kind = "module"]', style: {
      shape: 'round-rectangle',
      'background-color': colors.moduleBackground,
      'background-opacity': 0.55,
      'border-width': 1,
      'border-color': colors.moduleBorder,
      label: 'data(label)',
      color: colors.moduleText,
      'text-valign': 'top',
      'text-halign': 'center',
      'font-weight': 700,
      'font-size': 12,
      padding: '18px',
      'compound-sizing-wrt-labels': 'include',
    }},
    {selector: 'node[kind = "feature"]', style: {
      shape: 'round-rectangle',
      'background-color': colors.featureBackground,
      'border-width': 1.5,
      'border-color': colors.featureBorder,
      color: colors.featureText,
      label: 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'text-wrap': 'wrap',
      'text-max-width': '138px',
      // Explicit sizes: cytoscape 3.30+ deprecated `width`/`height: 'label'` (it warns and no longer
      // sizes the node to fit its label), which left nodes at a near-zero default size that antialiased
      // into a barely-visible smudge instead of a legible, solidly-filled rectangle.
      width: 150,
      height: 44,
      padding: '6px',
      'font-size': 10,
    }},
    {selector: 'node.is-selected', style: {'border-width': 3, 'border-color': colors.selected}},
    {selector: 'node.is-neighbor', style: {'border-width': 2.5, 'border-color': colors.selected}},
    {selector: '.is-dimmed', style: {opacity: 0.18}},
    ...EDGE_KINDS.map((kind) => ({
      selector: `edge[kind = "${kind}"]`,
      style: {
        width: kind === 'requires' ? 2.25 : 1.5,
        'line-color': colors.edge[kind],
        'target-arrow-color': colors.edge[kind],
        'target-arrow-shape': kind === 'relates_to' ? 'none' : 'triangle',
        'arrow-scale': 0.8,
        'line-style': kind === 'relates_to' ? 'dashed' : kind === 'requires' ? 'dotted' : 'solid',
        'curve-style': 'bezier',
        label: kind === 'requires' ? 'data(label)' : '',
        'font-size': 8,
        color: colors.edge[kind],
        'text-rotation': 'autorotate',
        'text-background-color': 'transparent',
      },
    })),
  ];
  return rules as unknown as cytoscape.StylesheetJson;
}

/** Highlights the selected feature's closed neighborhood and dims everything else; clears when unselected. */
function applySelection(cy: cytoscape.Core, selectedFeatureId?: string): void {
  cy.elements().removeClass('is-selected is-neighbor is-dimmed');
  if (!selectedFeatureId) return;
  const node = cy.getElementById(selectedFeatureId);
  if (node.empty()) return;
  const neighborhood = node.closedNeighborhood();
  // Only feature nodes and edges dim. A compound module node's opacity is inherited by every child it
  // contains, so dimming module groups would also fade the selected feature and its neighbors.
  cy.elements('node[kind = "feature"], edge').difference(neighborhood).addClass('is-dimmed');
  node.addClass('is-selected');
  neighborhood.difference(node).addClass('is-neighbor');
}

const FIT_PADDING = 24;

/**
 * Fits the viewport to every element with consistent padding, then raises the zoom toward
 * `minZoomAfterFit` so a sparse graph is never shrunk into illegibility (FR-007/NFR-002
 * readability) — but never past what the container can still show whole, so a larger, legitimately
 * spread-out graph (e.g. a well-connected feature's neighborhood) keeps every node on screen instead
 * of overflowing past the canvas edge. `fit`/`forceRender` also guarantee the first frame is actually
 * drawn before the effect returns, rather than deferred to a later animation frame the caller has no
 * way to wait for.
 */
function fitAndClampZoom(cy: cytoscape.Core, minZoomAfterFit: number): void {
  cy.fit(undefined, FIT_PADDING);
  const box = cy.elements().boundingBox();
  const maxZoomThatFits = Math.min(
    (cy.width() - 2 * FIT_PADDING) / box.w,
    (cy.height() - 2 * FIT_PADDING) / box.h,
  );
  const targetZoom = Math.min(minZoomAfterFit, maxZoomThatFits);
  if (Number.isFinite(targetZoom) && targetZoom > cy.zoom()) {
    cy.zoom(targetZoom);
    cy.center();
  }
  cy.forceRender();
}

/** Mounted only once cytoscape and cytoscape-fcose are loaded, so it never runs during server rendering. */
function CytoscapeCanvas({
  cy: cytoscapeCtor, fcose, modules, features, edges, selectedFeatureId, onSelect, height, minZoomAfterFit,
}: FeatureGraphProps & {cy: typeof cytoscape; fcose: cytoscape.Ext}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;
  const zoomFloor = minZoomAfterFit ?? 0.6;

  useEffect(() => {
    if (!containerRef.current) return undefined;
    try { cytoscapeCtor.use(fcose); } catch { /* Already registered by an earlier mount in this session. */ }
    const layout = {
      name: 'fcose', animate: false, nodeDimensionsIncludeLabels: true, quality: 'default', randomize: true,
      fit: false, // fitAndClampZoom below owns fit/zoom so it can also enforce the legibility floor.
      // A tighter, less-spread layout keeps more of the fit zoom's magnification for the nodes
      // themselves — important for a small neighborhood, where a handful of far-flung nodes would
      // otherwise force a much smaller zoom (and much smaller, harder-to-read nodes) than the node
      // count alone would need.
      nodeRepulsion: 2200,
      idealEdgeLength: 70,
      edgeElasticity: 0.35,
      nodeSeparation: 45,
      gravity: 0.6,
      gravityRange: 6,
      packComponents: true,
    } as unknown as cytoscape.LayoutOptions;
    const instance = cytoscapeCtor({
      container: containerRef.current,
      elements: toElements(modules, features, edges),
      style: buildStylesheet(readGraphColors()),
      layout,
      // No custom wheelSensitivity: cytoscape warns that a non-default value zooms unnaturally on
      // hardware other than the one it was tuned for.
      minZoom: 0.1,
      maxZoom: 3,
    });
    cyRef.current = instance;
    instance.on('tap', 'node[kind = "feature"]', (event) => onSelectRef.current?.(event.target.id() as string));
    instance.on('tap', (event) => { if (event.target === instance) onSelectRef.current?.(undefined); });
    fitAndClampZoom(instance, zoomFloor);
    applySelection(instance, selectedFeatureId);
    instance.forceRender();

    const observer = new MutationObserver(() => { instance.style(buildStylesheet(readGraphColors())); instance.forceRender(); });
    observer.observe(document.documentElement, {attributes: true, attributeFilter: ['data-theme']});

    return () => {
      observer.disconnect();
      instance.destroy();
      cyRef.current = null;
    };
    // Selection is applied by the effect below; rebuilding on every selection change would replay the layout.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cytoscapeCtor, fcose, modules, features, edges, zoomFloor]);

  useEffect(() => {
    if (cyRef.current) applySelection(cyRef.current, selectedFeatureId);
  }, [selectedFeatureId]);

  return (
    <div
      ref={containerRef}
      className="featureGraph__canvas"
      style={{height: height ?? '40rem'}}
      role="img"
      aria-label="Interactive feature relationship graph. The table below lists the same edges as text."
    />
  );
}

/**
 * Client-only Feature Graph renderer (`entity.auto-docs.graph-view`): module compound nodes, feature
 * nodes, and typed edges laid out with Cytoscape's fcose layout. Server-side rendering — and a client
 * with JavaScript disabled — instead gets a static placeholder; callers still render the textual edge
 * table so the same facts survive without the canvas.
 */
export default function FeatureGraph(props: FeatureGraphProps) {
  return (
    <BrowserOnly
      fallback={
        <div
          className="featureGraph__canvas featureGraph__placeholder"
          style={{height: props.height ?? '40rem'}}
          role="img"
          aria-label="Feature graph canvas placeholder. Enable JavaScript to view the interactive graph; the table below lists every edge as text."
        />
      }
    >
      {() => {
        // Loaded only in the browser: neither library is safe to touch during server rendering.
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const cytoscapeCtor = require('cytoscape') as typeof cytoscape;
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const fcoseModule = require('cytoscape-fcose') as {default?: cytoscape.Ext} & cytoscape.Ext;
        const fcose = (fcoseModule.default ?? fcoseModule) as cytoscape.Ext;
        return <CytoscapeCanvas cy={cytoscapeCtor} fcose={fcose} {...props} />;
      }}
    </BrowserOnly>
  );
}

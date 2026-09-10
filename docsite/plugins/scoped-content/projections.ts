/**
 * "Projections" pages: rendered views of the Concorde build's own `generated/docs/*.json`
 * outputs (proposal §12). These exist only for a project that itself builds and distributes
 * Concorde (today, only this repository's own dogfood docsite): an ordinary Profile 11 consumer
 * project has no `prompts/`/`skills/`/`capabilities/` of its own and therefore never produces
 * `generated/docs/instructions.json` or `generated/docs/wire.json`, so these pages are omitted
 * there rather than linking to content that was never materialized.
 *
 * Both pages are explicitly labelled projections: rendered bytes for human browsing, never a
 * second authoring source and never agent context authority. That promise lives in the
 * Development host boundary Spec, not here.
 */
import {existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {safeRead} from './model';

export const PROJECTION_NOTE =
  'This page is a rendered projection of the current build\'s `generated/docs/` output. It is a ' +
  'read-only view for human browsing, never a second authoring source, and never agent context ' +
  'authority — see the Development host boundary Spec for the promises these instructions and ' +
  'schemas actually keep.';

export interface SkillProjection {name: string; description: string; capability: string; body: string}
export interface ModeProjection {name: string; instructions: string; contract: Record<string, unknown>}
export interface AgentProjection {name: string; spec: string; harness: string; instructions: string; sources: string[]; modes: ModeProjection[]}
export interface InstructionsProjection {skills: SkillProjection[]; agents: AgentProjection[]}
export type WireProjection = Record<string, unknown>;

/** Whether this project root's Concorde build produced the docs projections at all. */
export function hasDocsProjections(root: string): boolean {
  return existsSync(resolve(root, 'generated/docs/instructions.json')) &&
    existsSync(resolve(root, 'generated/docs/wire.json'));
}

export function loadInstructionsProjection(root: string): InstructionsProjection {
  return JSON.parse(safeRead(root, 'generated/docs/instructions.json')) as InstructionsProjection;
}

export function loadWireProjection(root: string): WireProjection {
  return JSON.parse(safeRead(root, 'generated/docs/wire.json')) as WireProjection;
}

function fence(body: string, language: string): string {
  return '```' + language + '\n' + body.replace(/\n+$/, '') + '\n```';
}

export function renderInstructionsPage(doc: InstructionsProjection): string {
  const lines: string[] = ['# Agent instructions', '', PROJECTION_NOTE, ''];
  lines.push('## Skills', '', 'The eight public Skills expose global and lifecycle capabilities through `scripts/run-capability.py`.', '');
  for (const skill of doc.skills) {
    lines.push(`### ${skill.name}`, '', `Capability: \`${skill.capability}\`. ${skill.description}`, '', fence(skill.body, 'text'), '');
  }
  lines.push('## Agents', '', 'Each Agent binds common responsibilities, a Harness and an authority ceiling. Each invocation selects one explicit mode and receives only the common and selected mode instructions below.', '');
  for (const agent of doc.agents) {
    const sources = agent.sources.map((source) => `\`${source}\``).join(', ');
    lines.push(`### ${agent.name}`, '', `Spec: \`${agent.spec}\``, '', `Harness: \`${agent.harness}\``, '', `Contributing prompts: ${sources}`, '', fence(agent.instructions, 'text'), '');
    for (const mode of agent.modes) {
      lines.push(`#### ${agent.name} / ${mode.name}`, '', 'Mode contract:', '',
        fence(JSON.stringify(mode.contract, null, 2), 'json'), '',
        'Complete instructions for this mode:', '', fence(mode.instructions, 'text'), '');
    }
  }
  return lines.join('\n');
}

export function renderWirePage(doc: WireProjection): string {
  const lines: string[] = ['# Wire contracts', '', PROJECTION_NOTE, '',
    'Exact JSON Schemas for every identity `contracts.exported_types()` exports, rendered directly ' +
    'from code. The Development host boundary Spec states these types\' promise-level meaning; this ' +
    'page states their literal shape.', ''];
  for (const typeId of Object.keys(doc).sort()) {
    lines.push(`## ${typeId}`, '', fence(JSON.stringify(doc[typeId], null, 2), 'json'), '');
  }
  return lines.join('\n');
}

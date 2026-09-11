import {EventEmitter} from 'node:events';
import {beforeEach, expect, it, vi} from 'vitest';

const mocks = vi.hoisted(() => ({
  spawn: vi.fn(), rm: vi.fn(), rename: vi.fn(), stat: vi.fn(),
  requireScoped: vi.fn(), prepare: vi.fn(), validate: vi.fn(),
}));
vi.mock('node:child_process', () => ({spawn: mocks.spawn}));
vi.mock('node:fs/promises', () => ({rm: mocks.rm, rename: mocks.rename, stat: mocks.stat}));
vi.mock('../../plugins/scoped-content/model', () => ({requireScoped: mocks.requireScoped}));
vi.mock('../../plugins/scoped-content', () => ({validateScopedBuild: mocks.validate}));
vi.mock('../../scripts/prepare-publication', () => ({
  preparePublication: mocks.prepare,
  productionGeneratedDirectory: '.generated/docusaurus-production',
}));
import {buildSite, promoteCandidate} from '../../scripts/build';

beforeEach(() => {
  vi.resetAllMocks();
  mocks.stat.mockResolvedValue({});
  mocks.spawn.mockImplementation(() => {
    const child = new EventEmitter();
    queueMicrotask(() => child.emit('exit', 0));
    return child;
  });
});

it.each(['spawn', 'exit', 'validation', 'preparation'])(
  'scenario.views.build-site / scenario.views.publish-preserves-previous-on-failure: %s failure never promotes',
  async (failure) => {
    if (failure === 'preparation') mocks.prepare.mockRejectedValue(new Error('preparation failed'));
    if (failure === 'validation') mocks.validate.mockRejectedValue(new Error('stale candidate'));
    if (failure === 'spawn' || failure === 'exit') mocks.spawn.mockImplementation(() => {
      const child = new EventEmitter();
      queueMicrotask(() => failure === 'spawn'
        ? child.emit('error', new Error('spawn failed')) : child.emit('exit', 1));
      return child;
    });
    await expect(buildSite()).rejects.toThrow();
    expect(mocks.rename).not.toHaveBeenCalled();
    expect(mocks.rm.mock.calls.every(([path]) => path.endsWith('/.generated/candidate'))).toBe(true);
    if (failure !== 'validation') expect(mocks.validate).not.toHaveBeenCalled();
  },
);

it('scenario.views.build-site: validation precedes directory replacement and production isolates generated modules', async () => {
  await buildSite();
  expect(mocks.validate.mock.invocationCallOrder[0]).toBeLessThan(mocks.rename.mock.invocationCallOrder[0]);
  expect(mocks.prepare).toHaveBeenCalledWith(expect.any(String), {mode: 'build'});
  expect(mocks.spawn.mock.calls[0][2].env.DOCUSAURUS_GENERATED_FILES_DIR_NAME).toBe('.generated/docusaurus-production');
});

it('scenario.views.build-site: failed backup removal attempts to restore the previous destination', async () => {
  mocks.rm.mockResolvedValue(undefined).mockResolvedValueOnce(undefined).mockRejectedValueOnce(new Error('remove failed'));
  await expect(promoteCandidate('candidate', 'destination', 'backup')).rejects.toThrow('remove failed');
  expect(mocks.rename.mock.calls).toEqual([
    ['destination', 'backup'], ['candidate', 'destination'], ['backup', 'destination'],
  ]);
  expect(mocks.rm).toHaveBeenCalledWith('destination', {recursive: true, force: true});
});

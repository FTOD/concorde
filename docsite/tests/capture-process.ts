import {spawnSync, type SpawnSyncOptions} from 'node:child_process';
import {closeSync, mkdtempSync, openSync, readFileSync, rmSync} from 'node:fs';
import {resolve} from 'node:path';

/** Capture diagnostics without Node's pipe sockets, which restricted runners may deny. */
export function captureProcess(
  command: string,
  args: string[],
  options: Pick<SpawnSyncOptions, 'env' | 'timeout'> & {cwd: string},
) {
  const directory = mkdtempSync(resolve(options.cwd, '.test-stdio-'));
  const stdoutPath = resolve(directory, 'stdout');
  const stderrPath = resolve(directory, 'stderr');
  try {
    const stdoutFd = openSync(stdoutPath, 'wx');
    let result;
    try {
      const stderrFd = openSync(stderrPath, 'wx');
      try {
        result = spawnSync(command, args, {...options, stdio: ['ignore', stdoutFd, stderrFd]});
      } finally {
        closeSync(stderrFd);
      }
    } finally {
      closeSync(stdoutFd);
    }
    const stdout = readFileSync(stdoutPath, 'utf8');
    const stderr = readFileSync(stderrPath, 'utf8');
    return {...result, stdout, stderr, output: [null, stdout, stderr]};
  } finally {
    rmSync(directory, {recursive: true, force: true});
  }
}

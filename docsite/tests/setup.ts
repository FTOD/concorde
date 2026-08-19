import {afterEach} from 'vitest';

afterEach(() => {
  delete process.env.CONCORDE_PROJECT_ROOT;
  delete process.env.CONCORDE_BUILD_OUT_DIR;
});


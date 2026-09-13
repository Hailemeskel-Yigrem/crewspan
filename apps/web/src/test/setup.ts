import '@testing-library/jest-dom';
import { afterEach, beforeEach, vi } from 'vitest';

// Pages fetch on mount. Without a default stub the suite makes real network
// calls, and the rejected promises surface as unhandled errors that fail the
// run. Tests that assert on a response override this with their own mock.
const emptyPage = { data: [], total: 0, page: 1, pageSize: 50, pages: 1 };

beforeEach(() => {
  vi.stubGlobal('matchMedia', vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  })));

  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    statusText: 'OK',
    json: async () => emptyPage,
  }));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

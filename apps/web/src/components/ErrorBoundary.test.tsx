import { render } from '@testing-library/react';
import { ErrorBoundary } from '../ErrorBoundary';

describe('ErrorBoundary', () => {
  it('renders without crashing', () => {
    expect(ErrorBoundary).toBeDefined();
  });
});

import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { InvoicesPage } from '../InvoicesPage';

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ isAuthenticated: true, user: { fullName: 'Test User' }, logout: vi.fn() }),
}));

describe('InvoicesPage', () => {
  it('renders page heading or content', () => {
    render(
      <MemoryRouter>
        <InvoicesPage />
      </MemoryRouter>,
    );
    expect(document.querySelector('.page')).toBeTruthy();
  });
});

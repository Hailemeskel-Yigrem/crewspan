import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { AuditLogPage } from '../AuditLogPage';

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ isAuthenticated: true, user: { fullName: 'Test User' }, logout: vi.fn() }),
}));

describe('AuditLogPage', () => {
  it('renders page heading or content', () => {
    render(
      <MemoryRouter>
        <AuditLogPage />
      </MemoryRouter>,
    );
    expect(document.querySelector('.page')).toBeTruthy();
  });
});

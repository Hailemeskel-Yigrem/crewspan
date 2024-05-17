import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { NotificationsPage } from '../NotificationsPage';

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ isAuthenticated: true, user: { fullName: 'Test User' }, logout: vi.fn() }),
}));

describe('NotificationsPage', () => {
  it('renders page heading or content', () => {
    render(
      <MemoryRouter>
        <NotificationsPage />
      </MemoryRouter>,
    );
    expect(document.querySelector('.page')).toBeTruthy();
  });
});

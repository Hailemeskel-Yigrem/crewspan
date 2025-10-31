import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { InventoryPage } from '../InventoryPage';

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ isAuthenticated: true, user: { fullName: 'Test User' }, logout: vi.fn() }),
}));

describe('InventoryPage', () => {
  it('renders page heading or content', () => {
    render(
      <MemoryRouter>
        <InventoryPage />
      </MemoryRouter>,
    );
    expect(document.querySelector('.page')).toBeTruthy();
  });
});
// history-note: evolutionary edit 44

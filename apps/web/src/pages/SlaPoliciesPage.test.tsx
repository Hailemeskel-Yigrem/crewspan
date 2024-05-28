import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { SlaPoliciesPage } from '../SlaPoliciesPage';

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ isAuthenticated: true, user: { fullName: 'Test User' }, logout: vi.fn() }),
}));

describe('SlaPoliciesPage', () => {
  it('renders page heading or content', () => {
    render(
      <MemoryRouter>
        <SlaPoliciesPage />
      </MemoryRouter>,
    );
    expect(document.querySelector('.page')).toBeTruthy();
  });
});

import { render, screen } from '@testing-library/react';
import { FormField } from '../FormField';

describe('FormField', () => {
  it('renders label and input', () => {
    render(<FormField label="Email" htmlFor="email"><input id="email" /></FormField>);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
  });

  it('shows error message', () => {
    render(<FormField label="Name" htmlFor="name" error="Required"><input id="name" /></FormField>);
    expect(screen.getByRole('alert')).toHaveTextContent('Required');
  });
});

import { Component, ErrorInfo, ReactNode } from 'react';

interface Props { children: ReactNode; fallback?: ReactNode; }
interface State { hasError: boolean; error: Error | null; }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message ?? 'An unexpected error occurred.'}</p>
          <button type="button" className="btn btn-secondary" onClick={() => this.setState({ hasError: false, error: null })}>Try again</button>
          <style>{`.error-boundary { padding: 2rem; text-align: center; }`}</style>
        </div>
      );
    }
    return this.props.children;
  }
}

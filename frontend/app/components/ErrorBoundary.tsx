"use client";

import { Component, ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

interface ErrorBoundaryProps {
  children: ReactNode;
  label?: string;
}

interface ErrorBoundaryState {
  error: Error | null;
}

/**
 * Wraps a section of the dashboard so an unexpected data shape from one
 * panel (e.g. a real API response that doesn't match what was tested)
 * can't silently blank out the rest of the page - React unmounts the whole
 * tree above the nearest error boundary on an uncaught render error, which
 * without this looks exactly like "the site is just static/broken."
 */
export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    console.error(`[ErrorBoundary${this.props.label ? `: ${this.props.label}` : ""}]`, error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm">
          <div className="flex items-center gap-2 text-accent-red font-medium mb-1">
            <AlertTriangle className="w-4 h-4" />
            {this.props.label || "This section"} failed to render
          </div>
          <p className="text-grayish text-xs">
            {this.state.error.message || "Unexpected error"} - check the browser console for details.
            The rest of the page should still work.
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}

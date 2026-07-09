"use client";

import { useEffect } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("[Route error]", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-light flex items-center justify-center px-6">
      <div className="max-w-md w-full p-6 bg-white rounded-lg border border-beige text-center">
        <AlertTriangle className="w-8 h-8 text-accent-red mx-auto mb-3" />
        <h2 className="text-lg font-bold text-dark mb-1">Something went wrong</h2>
        <p className="text-sm text-grayish mb-4">
          {error.message || "An unexpected error occurred rendering this page."} Check the browser
          console (F12) for the full stack trace, and the backend terminal for any related errors.
        </p>
        <Button onClick={reset} className="bg-dark text-white hover:bg-dark/90">
          <RotateCcw className="w-4 h-4" /> Try again
        </Button>
      </div>
    </div>
  );
}

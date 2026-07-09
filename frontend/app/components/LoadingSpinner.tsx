"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Brain, TrendingUp, MessageSquare } from "lucide-react";

export default function LoadingSpinner() {
  return (
    <div className="w-full max-w-6xl mx-auto space-y-4">
      {/* Main Loading Card - More Compact */}
      <Card className="bg-light border-beige">
        <CardContent className="py-8">
          <div className="flex flex-col items-center text-center">
            <div className="relative mb-4">
              <Brain className="w-8 h-8 text-accent-red animate-pulse" />
              <div className="absolute inset-0 w-8 h-8 border-2 border-accent-red border-t-transparent rounded-full animate-spin"></div>
            </div>
            <h3 className="text-lg font-semibold text-dark mb-2">
              Analyzing Market Sentiment
            </h3>
            <p className="text-sm text-grayish mb-4">
              AI is processing data from multiple sources...
            </p>
            
            {/* Progress Steps - Horizontal */}
            <div className="flex items-center justify-center space-x-6 mb-4">
              <div className="flex flex-col items-center space-y-1">
                <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center animate-pulse">
                  <TrendingUp className="w-3 h-3 text-white" />
                </div>
                <span className="text-xs text-grayish">Yahoo</span>
              </div>
              <div className="flex flex-col items-center space-y-1">
                <div className="w-6 h-6 bg-orange-500 rounded-full flex items-center justify-center animate-pulse">
                  <MessageSquare className="w-3 h-3 text-white" />
                </div>
                <span className="text-xs text-grayish">Reddit</span>
              </div>
              <div className="flex flex-col items-center space-y-1">
                <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center animate-pulse">
                  <span className="text-white text-xs font-bold">𝕏</span>
                </div>
                <span className="text-xs text-grayish">Twitter</span>
              </div>
            </div>
            
            {/* Loading Bar */}
            <div className="w-full max-w-xs bg-beige rounded-full h-1.5 overflow-hidden">
              <div className="bg-accent-red h-full rounded-full animate-pulse" style={{
                animation: 'loading 2s ease-in-out infinite',
                width: '60%'
              }}></div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Skeleton Cards - Arranged in Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="bg-light border-beige">
            <CardHeader className="pb-3">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-beige rounded animate-pulse"></div>
                <div className="space-y-1 flex-1">
                  <div className="h-3 bg-beige rounded animate-pulse w-1/3"></div>
                  <div className="h-2 bg-beige rounded animate-pulse w-1/4"></div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-2">
                <div className="h-3 bg-beige rounded animate-pulse w-3/4"></div>
                <div className="h-2 bg-beige rounded animate-pulse w-1/2"></div>
                <div className="flex space-x-2 mt-3">
                  <div className="h-4 bg-beige rounded animate-pulse w-12"></div>
                  <div className="h-4 bg-beige rounded animate-pulse w-16"></div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <style jsx>{`
        @keyframes loading {
          0% { width: 10%; }
          50% { width: 70%; }
          100% { width: 10%; }
        }
      `}</style>
    </div>
  );
}

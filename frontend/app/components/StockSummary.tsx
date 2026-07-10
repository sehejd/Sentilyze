"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Minus, Brain, Clock } from "lucide-react";
import PanelIcon from "./PanelIcon";

interface StockSummaryProps {
  ticker: string;
  analysis: {
    overall_sentiment?: {
      sentiment: string;
      confidence: number;
      positive: number;
      negative: number;
      neutral: number;
    };
    ai_summary?: string;
    summary?: string;
    analysis_timestamp?: string;
    confidence_score?: number;
  };
}

export default function StockSummary({ ticker, analysis }: StockSummaryProps) {
  const getSentimentColor = (sentiment: string) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return 'bg-green-500';
      case 'negative':
        return 'bg-[#eb5e28]';
      default:
        return 'bg-yellow-400';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return <TrendingUp className="w-4 h-4" />;
      case 'negative':
        return <TrendingDown className="w-4 h-4" />;
      default:
        return <Minus className="w-4 h-4" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return 'Just now';
    }
  };

  const sentiment = analysis?.overall_sentiment?.sentiment || 'neutral';
  const confidence = analysis?.overall_sentiment?.confidence || 0;
  const aiSummary = analysis?.ai_summary;
  const fallbackSummary = analysis?.summary;

  return (
    <div className="w-full max-w-6xl mx-auto space-y-4">
      {/* Header Card - More Compact */}
      <Card className="bg-light border-beige">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <CardTitle className="text-xl font-bold text-dark">
                ${ticker.toUpperCase()} Analysis
              </CardTitle>
              <CardDescription className="text-grayish text-sm">
                AI-powered sentiment analysis
              </CardDescription>
            </div>
            <div className="flex items-center gap-3">
              <Badge 
                className={`${getSentimentColor(sentiment)} text-white flex items-center gap-1 px-2 py-1 text-xs`}
              >
                {getSentimentIcon(sentiment)}
                {sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
              </Badge>
              <div className="text-xs text-grayish">
                {Math.round(confidence * 100)}% confidence
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* AI Summary - Takes up 2 columns on large screens */}
        {(aiSummary || fallbackSummary) && (
          <Card className="bg-light border-beige lg:col-span-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold text-dark flex items-center gap-3">
                <PanelIcon><Brain className="w-4 h-4" /></PanelIcon>
                AI Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none text-grayish">
                <p className="text-sm leading-relaxed line-clamp-4">
                  {aiSummary ? 
                    aiSummary.length > 400 ? aiSummary.substring(0, 400) + '...' : aiSummary
                    : 
                    fallbackSummary ? 
                      fallbackSummary.length > 400 ? fallbackSummary.substring(0, 400) + '...' : fallbackSummary
                      : ''
                  }
                </p>
              </div>
              {analysis?.analysis_timestamp && (
                <div className="flex items-center gap-1 mt-3 pt-3 border-t border-beige text-xs text-grayish">
                  <Clock className="w-3 h-3" />
                  <span>{formatTimestamp(analysis.analysis_timestamp)}</span>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Sentiment Breakdown - Takes up 1 column */}
        {analysis?.overall_sentiment && (
          <Card className="bg-light border-beige">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold text-dark">
                Sentiment Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-2 bg-green-50 rounded border border-green-200">
                  <span className="text-xs font-medium text-green-800">Positive</span>
                  <span className="text-sm font-bold text-green-600">
                    {Math.round((analysis.overall_sentiment.positive || 0) * 100)}%
                  </span>
                </div>
                <div className="flex items-center justify-between p-2 bg-yellow-50 rounded border border-yellow-200">
                  <span className="text-xs font-medium text-yellow-800">Neutral</span>
                  <span className="text-sm font-bold text-yellow-600">
                    {Math.round((analysis.overall_sentiment.neutral || 0) * 100)}%
                  </span>
                </div>
                <div className="flex items-center justify-between p-2 bg-red-50 rounded border border-red-200">
                  <span className="text-xs font-medium text-red-800">Negative</span>
                  <span className="text-sm font-bold text-red-600">
                    {Math.round((analysis.overall_sentiment.negative || 0) * 100)}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

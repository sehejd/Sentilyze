"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ChevronDown,
  ChevronUp,
  MessageSquare,
  TrendingUp,
  Calendar,
  Heart,
  Repeat
} from "lucide-react";
import { useState } from "react";

interface HeadlineData {
  title: string;
  summary?: string;
  url?: string;
  timestamp?: string;
  source?: string;
}

interface RedditPost {
  title: string;
  text?: string;
  url?: string;
  score?: number;
  created_utc?: number;
  subreddit?: string;
  author?: string;
}

interface TwitterTweet {
  text: string;
  likes?: number;
  retweets?: number;
  timestamp?: string;
  username?: string;
}

interface RawData {
  yahoo_finance?: {
    success: boolean;
    headlines?: HeadlineData[];
    total_found?: number;
  };
  reddit?: {
    success: boolean;
    posts?: RedditPost[];
    total_found?: number;
  };
  twitter?: {
    success: boolean;
    tweets?: TwitterTweet[];
    total_found?: number;
  };
}

interface HeadlineListProps {
  rawData: RawData;
  ticker: string;
}

export default function HeadlineList({ rawData }: HeadlineListProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    yahoo: true,
    reddit: false,
    twitter: false,
  });

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const formatTimestamp = (timestamp: string | number) => {
    try {
      const date = typeof timestamp === 'number' ? new Date(timestamp * 1000) : new Date(timestamp);
      return date.toLocaleDateString();
    } catch {
      return 'Recently';
    }
  };

  const getSentimentBadge = (text: string) => {
    const lowerText = text.toLowerCase();
    const positiveWords = ['bullish', 'buy', 'moon', 'rocket', 'pump', 'gain', 'profit', 'strong', 'growth'];
    const negativeWords = ['bearish', 'sell', 'crash', 'dump', 'short', 'loss', 'weak', 'decline'];
    
    const hasPositive = positiveWords.some(word => lowerText.includes(word));
    const hasNegative = negativeWords.some(word => lowerText.includes(word));
    
    if (hasPositive && !hasNegative) {
      return <Badge className="bg-green-500 text-white">Positive</Badge>;
    } else if (hasNegative && !hasPositive) {
      return <Badge className="bg-[#eb5e28] text-white">Negative</Badge>;
    } else {
      return <Badge className="bg-yellow-400 text-white">Neutral</Badge>;
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Yahoo Finance Section */}
        {rawData.yahoo_finance?.success && (
          <Card className="bg-light border-beige">
            <CardHeader 
              className="cursor-pointer pb-3"
              onClick={() => toggleSection('yahoo')}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-accent" />
                  <div>
                    <CardTitle className="text-sm font-semibold text-dark">
                      Yahoo Finance
                    </CardTitle>
                    <CardDescription className="text-xs text-grayish">
                      {rawData.yahoo_finance.total_found || rawData.yahoo_finance.headlines?.length || 0} headlines
                    </CardDescription>
                  </div>
                </div>
                {expandedSections.yahoo ? 
                  <ChevronUp className="w-4 h-4 text-grayish" /> : 
                  <ChevronDown className="w-4 h-4 text-grayish" />
                }
              </div>
            </CardHeader>
            {expandedSections.yahoo && (
              <CardContent className="pt-0">
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {rawData.yahoo_finance.headlines?.slice(0, 5).map((headline, index) => (
                    <div 
                      key={index}
                      className="p-3 bg-white rounded border border-beige hover:shadow-sm transition-shadow"
                    >
                      <h4 className="font-medium text-dark text-sm mb-1 line-clamp-2">
                        {headline.title}
                      </h4>
                      {headline.summary && (
                        <p className="text-xs text-grayish mb-2 line-clamp-2">
                          {headline.summary}
                        </p>
                      )}
                      <div className="flex items-center justify-between">
                        {getSentimentBadge(headline.title + ' ' + (headline.summary || ''))}
                        {headline.timestamp && (
                          <div className="flex items-center gap-1 text-xs text-grayish">
                            <Calendar className="w-3 h-3" />
                            {formatTimestamp(headline.timestamp)}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            )}
          </Card>
        )}

        {/* Reddit Section */}
        {rawData.reddit?.success && (
          <Card className="bg-light border-beige">
            <CardHeader 
              className="cursor-pointer pb-3"
              onClick={() => toggleSection('reddit')}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-orange-500" />
                  <div>
                    <CardTitle className="text-sm font-semibold text-dark">
                      Reddit
                    </CardTitle>
                    <CardDescription className="text-xs text-grayish">
                      {rawData.reddit.total_found || rawData.reddit.posts?.length || 0} posts
                    </CardDescription>
                  </div>
                </div>
                {expandedSections.reddit ? 
                  <ChevronUp className="w-4 h-4 text-grayish" /> : 
                  <ChevronDown className="w-4 h-4 text-grayish" />
                }
              </div>
            </CardHeader>
            {expandedSections.reddit && (
              <CardContent className="pt-0">
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {rawData.reddit.posts?.slice(0, 5).map((post, index) => (
                    <div 
                      key={index}
                      className="p-3 bg-white rounded border border-beige hover:shadow-sm transition-shadow"
                    >
                      <h4 className="font-medium text-dark text-sm mb-1 line-clamp-2">
                        {post.title}
                      </h4>
                      {post.text && (
                        <p className="text-xs text-grayish mb-2 line-clamp-2">
                          {post.text}
                        </p>
                      )}
                      <div className="flex items-center justify-between">
                        {getSentimentBadge(post.title + ' ' + (post.text || ''))}
                        <div className="flex items-center gap-2 text-xs text-grayish">
                          {post.score && (
                            <div className="flex items-center gap-1">
                              <TrendingUp className="w-3 h-3" />
                              {post.score}
                            </div>
                          )}
                          {post.subreddit && (
                            <span>r/{post.subreddit}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            )}
          </Card>
        )}

        {/* Twitter Section */}
        {rawData.twitter?.success && (
          <Card className="bg-light border-beige">
            <CardHeader 
              className="cursor-pointer pb-3"
              onClick={() => toggleSection('twitter')}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-xs font-bold">𝕏</span>
                  </div>
                  <div>
                    <CardTitle className="text-sm font-semibold text-dark">
                      Twitter/X
                    </CardTitle>
                    <CardDescription className="text-xs text-grayish">
                      {rawData.twitter.total_found || rawData.twitter.tweets?.length || 0} tweets
                    </CardDescription>
                  </div>
                </div>
                {expandedSections.twitter ? 
                  <ChevronUp className="w-4 h-4 text-grayish" /> : 
                  <ChevronDown className="w-4 h-4 text-grayish" />
                }
              </div>
            </CardHeader>
            {expandedSections.twitter && (
              <CardContent className="pt-0">
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {rawData.twitter.tweets?.slice(0, 5).map((tweet, index) => (
                    <div 
                      key={index}
                      className="p-3 bg-white rounded border border-beige hover:shadow-sm transition-shadow"
                    >
                      <p className="text-sm text-dark mb-2 line-clamp-3">
                        {tweet.text}
                      </p>
                      <div className="flex items-center justify-between">
                        {getSentimentBadge(tweet.text)}
                        <div className="flex items-center gap-2 text-xs text-grayish">
                          {tweet.likes && (
                            <div className="flex items-center gap-1">
                              <Heart className="w-3 h-3" />
                              {tweet.likes}
                            </div>
                          )}
                          {tweet.retweets && (
                            <div className="flex items-center gap-1">
                              <Repeat className="w-3 h-3" />
                              {tweet.retweets}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}

import type { Metadata } from "next";
import { Geist, Geist_Mono, Limelight } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const limelight = Limelight({
  variable: "--font-limelight",
  weight: "400",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Sentilyze - Real-Time Stock Sentiment Engine",
  description: "Sentiment, fundamentals, insider activity, geopolitics & social momentum, blended into one score.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${limelight.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}

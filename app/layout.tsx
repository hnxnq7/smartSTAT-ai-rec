import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'smartSTAT - AI Recommendations',
  description: 'Medication management dashboard with AI-powered recommendations',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}








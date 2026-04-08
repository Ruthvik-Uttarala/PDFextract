import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "PDFextract",
  description: "Phase 0 and Phase 1 foundation scaffold for PDFextract."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

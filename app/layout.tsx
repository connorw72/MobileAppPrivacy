import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mobile App Privacy",
  description: "Search iOS apps and score their privacy disclosures."
};

export default function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}


import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ReverseEngineer-SDLC",
  description: "Reverse engineer GitHub repositories into SDLC documentation.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}

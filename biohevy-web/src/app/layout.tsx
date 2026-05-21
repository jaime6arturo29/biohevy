import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "BioHevy — Biomechanical Fitness Engine",
  description: "Sistema avanzado de seguimiento de hipertrofia con análisis biomecánico EMG en tiempo real.",
};

import { ClerkProvider, SignInButton, SignUpButton, Show } from "@clerk/nextjs";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <ClerkProvider>
          <Show when="signed-out">
            <header className="p-4 flex justify-end gap-4 border-b border-gray-800 bg-black">
              <div className="text-white">
                <SignInButton />
              </div>
              <div className="bg-white text-black px-4 py-1 rounded-full font-bold">
                <SignUpButton />
              </div>
            </header>
          </Show>
          {children}
        </ClerkProvider>
      </body>
    </html>
  );
}

import type {Metadata} from 'next';
import { Outfit, JetBrains_Mono } from 'next/font/google';
import './globals.css'; // Global styles

const outfit = Outfit({
  subsets: ['latin'],
  variable: '--font-outfit',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
});

export const metadata: Metadata = {
  title: 'Ana - Swahili Voice AI',
  description: 'Swahili Voice AI Assistant',
};

export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html lang="en" className={`${outfit.variable} ${jetbrainsMono.variable}`}>
       <body className="font-sans antialiased bg-[#0a0505] text-white" suppressHydrationWarning>{children}</body>
    </html>
  );
}

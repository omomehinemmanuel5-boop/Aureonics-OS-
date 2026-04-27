import './globals.css';
import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Lex Aureon — AI Trust Layer',
  description: 'Lex intercepts, stabilizes, and improves AI responses in real-time.'
};

const navItems = [
  { href: '/', label: 'Home' },
  { href: '/demo', label: 'Demo' },
  { href: '/pricing', label: 'Pricing' },
  { href: '/app', label: 'Dashboard' }
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-slate-200 bg-white/95 backdrop-blur">
          <div className="container-shell flex h-16 items-center justify-between">
            <Link href="/" className="text-lg font-semibold tracking-tight">
              Lex Aureon
            </Link>
            <nav className="flex gap-5 text-sm text-slate-600">
              {navItems.map((item) => (
                <Link key={item.href} href={item.href} className="hover:text-slate-900">
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}

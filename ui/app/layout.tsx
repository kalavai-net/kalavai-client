import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthInitializer } from '@/components/AuthInitializer';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Kalavai Platform UI',
  description: 'Kalavai Client Platform UI for managing GPU pools and AI workloads',
  icons: { icon: '/favicon.ico' },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <script dangerouslySetInnerHTML={{ __html: `
          (function() {
            try {
              var stored = localStorage.getItem('kalavai-theme-storage');
              var dark = true;
              if (stored) {
                var parsed = JSON.parse(stored);
                if (parsed && parsed.state && typeof parsed.state.darkMode === 'boolean') {
                  dark = parsed.state.darkMode;
                }
              }
              document.documentElement.classList.add(dark ? 'dark' : 'light');
            } catch(e) {
              document.documentElement.classList.add('dark');
            }
            
            // Inject environment variables
            window.env = window.env || {};
            window.env.SHOW_RESOURCES = "${process.env.SHOW_RESOURCES || 'true'}";
            window.env.SHOW_MONITORING = "${process.env.SHOW_MONITORING || 'true'}";
            window.env.SHOW_USER_SPACES = "${process.env.SHOW_USER_SPACES || 'true'}";
          })();
        `}} />
      </head>
      <body className={inter.className}>
        <AuthInitializer />
        {children}
      </body>
    </html>
  );
}

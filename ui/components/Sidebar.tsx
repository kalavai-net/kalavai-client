'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  LayoutDashboard,
  Cpu,
  Settings,
  Briefcase,
  Server,
  LogOut,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAuthStore } from '@/stores';

const navigation = [
  { name: 'Home', href: '/', icon: Home },
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Resources', href: '/resources', icon: Cpu },
  { name: 'Jobs', href: '/jobs', icon: Briefcase },
  { name: 'Services', href: '/services', icon: Server },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { signOut } = useAuthStore();

  return (
    <div className="hidden md:flex md:flex-col md:w-64 md:bg-card md:border-r md:border-border md:min-h-screen">
      <div className="flex items-center h-16 px-4 border-b border-border">
        <Link href="/" className="flex items-center">
          <img src="/logo.png" alt="Kalavai" className="h-8 w-auto" />
        </Link>
      </div>
      
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <Icon className="w-5 h-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
      
      <div className="p-3 border-t border-border">
        <button
          onClick={signOut}
          className="flex items-center gap-3 px-3 py-2 w-full rounded-md text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
        >
          <LogOut className="w-5 h-5" />
          Sign Out
        </button>
      </div>
    </div>
  );
}

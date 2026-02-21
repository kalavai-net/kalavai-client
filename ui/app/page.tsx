'use client';

import Link from 'next/link';
import { useAuthStore } from '@/stores';
import { LoginForm } from '@/components/LoginForm';
import { AppLayout } from '@/components/AppLayout';
import { UserSpaceQuota } from '@/components/UserSpaceQuota';
import { Computer, Cpu, Anchor, BookOpen, Loader2 } from 'lucide-react';

const ACCESS_KEY = process.env.NEXT_PUBLIC_ACCESS_KEY || null;

function IntroCard({
  title,
  icon: Icon,
  text,
  href,
  isExternal = false,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  text: string;
  href: string;
  isExternal?: boolean;
}) {
  const content = (
    <div className="bg-card border border-border rounded-lg p-6 hover:border-primary/50 transition-colors cursor-pointer h-full">
      <div className="flex items-center gap-3 mb-3">
        <Icon className="w-8 h-8 text-primary" />
        <h3 className="font-semibold text-lg">{title}</h3>
      </div>
      <p className="text-sm text-muted-foreground">{text}</p>
    </div>
  );

  if (isExternal) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className="block">
        {content}
      </a>
    );
  }

  return <Link href={href}>{content}</Link>;
}

function HomeContent() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-1">Welcome to Kalavai!</h1>
        <p className="text-muted-foreground">
          Here are a few links to get you going.
        </p>
      </div>

      <UserSpaceQuota />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <IntroCard
          title="Explore your resources"
          icon={Computer}
          text="Visit the dashboard for a high level overview of your Kalavai pool"
          href="/dashboard"
        />
        <IntroCard
          title="Add resources to your pool"
          icon={Cpu}
          text="Want to add your own devices to the pool? Check out how"
          href="https://kalavai-net.github.io/kalavai-client/getting_started/#2-add-worker-nodes"
          isExternal
        />
        <IntroCard
          title="Deploy jobs and models"
          icon={Anchor}
          text="Put your resources to work by deploying models and workloads with our ready-made templates"
          href="/jobs"
        />
        <IntroCard
          title="Kalavai documentation"
          icon={BookOpen}
          text="Explore what Kalavai has to offer"
          href="https://kalavai-net.github.io/kalavai-client/"
          isExternal
        />
      </div>
    </div>
  );
}

export default function HomePage() {
  const { isLoggedIn, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!isLoggedIn) {
    return <LoginForm accessKey={ACCESS_KEY || undefined} />;
  }

  return (
    <AppLayout>
      <HomeContent />
    </AppLayout>
  );
}

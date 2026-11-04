'use client';
import type { ReactNode } from 'react';

// Inherit the shared French document/navigation; do not nest html/body tags.
export default function ProfileLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

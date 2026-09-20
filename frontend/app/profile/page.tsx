
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ProfileWorkspace } from "../profile-workspace";

export default function ProfilePage() {
  const [token, setToken] = useState<string | null>(null);
  const router = useRouter();
  useEffect(() => { const value = window.sessionStorage.getItem("jobpilot_token"); if (!value) router.replace("/"); else setToken(value); }, [router]);
  const expire = () => { window.sessionStorage.removeItem("jobpilot_token"); router.replace("/"); };
  if (!token) return <main className="profile-loading" aria-live="polite">Loading your private profile workspace…</main>;
  return <main className="profile-page"><header><div><p>PRIVATE WORKSPACE</p><h1>Profile &amp; resumes</h1></div><Link href="/">Back to dashboard</Link></header><ProfileWorkspace token={token} onExpired={expire} /></main>;
}

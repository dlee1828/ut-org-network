'use client'
import { Button, Card, NextUIProvider } from "@nextui-org/react";
import Image from 'next/image'
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  return (
    <NextUIProvider>
      <div className="flex flex-col items-center pt-12 gap-8">
        <h1 className="text-5xl font-bold leading-relaxed py-1 bg-gradient-to-r from-orange-400 to-orange-600 text-transparent bg-clip-text">UT Org Network</h1>
        <Button>Log In</Button>
        <Button onClick={() => router.push('/sign-up')}>Sign Up</Button>
        <Button>Explore</Button>
      </div>
    </NextUIProvider>
  )
}

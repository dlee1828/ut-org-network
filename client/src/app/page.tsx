'use client'
import { Button, NextUIProvider } from "@nextui-org/react";
import Image from 'next/image'

export default function Home() {
  return (
    <NextUIProvider>
      <div className="flex flex-col items-center pt-12">
        <h1>UT Org Network</h1>
        <Button>Log In</Button>
        <Button>Sign Up</Button>
        <Button>Explore</Button>
      </div>
    </NextUIProvider>
  )
}

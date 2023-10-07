'use client'

import { Button } from "@nextui-org/react"
import { useRouter } from "next/navigation"

export default function Home() {
  const router = useRouter();

  const handleEditProfileClicked = () => {
    router.push('/edit-profile');
  }

  const handleGetRecommendationsClicked = () => {

  }

  const handleSignOutClicked = () => {
    router.push('/');
  }

  return <div className="flex flex-col items-center pt-28 gap-8">
    <div className="text-3xl pb-8">Hi Daniel! What would you like to do?</div>
    <Button onClick={handleEditProfileClicked} radius="full" className="h-16 w-60 text-lg bg-gradient-to-tr from-blue-500 to-pink-500 text-white shadow-lg">Edit My Profile</Button>
    <Button radius="full" className="h-16 w-60 text-lg bg-gradient-to-tr from-pink-500 to-yellow-500 text-white shadow-lg">Get Recommendations!</Button>
    <Button onClick={handleSignOutClicked} radius="full" className="shadow-lg" color="primary">Sign Out</Button>
  </div>
}
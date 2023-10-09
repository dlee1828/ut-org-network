'use client'

import { Button, Spinner } from "@nextui-org/react";
import Loader from "./loader";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import RecommendedOrganization from "./recommended-organization";
import { sampleRecommendedOrganizations } from "./sample-data";

export default function GetRecommendations() {
  const router = useRouter()
  const [recommendationLoading, setRecommendationsLoading] = useState<boolean>(true);
  const [backButtonLoading, setBackButtonLoading] = useState<boolean>(false);

  useEffect(() => {
    setTimeout(() => {
      setRecommendationsLoading(false);
    }, 1000);
  }, [])

  const handleBackButtonClicked = () => {
    setBackButtonLoading(true);
    router.push('/home');
  }

  return <div className="flex flex-col items-center gap-4 py-20">
    {
      recommendationLoading ? <>
        <Loader />
        <div>Computing your recommendations...</div>
      </> : <>
        <h4 className="animate-fadeIn opacity-0">Here are a few organizations you might be interested in:</h4>
        <div className="flex flex-col items-center gap-4">
          {sampleRecommendedOrganizations.map((org, index) => <RecommendedOrganization key={index} data={org} style={{ animationDelay: `${(index + 1) * 500}ms` }} />)}
        </div>
        <Button isLoading={backButtonLoading} onClick={handleBackButtonClicked} color="primary" radius="full" style={{ animationDelay: `${(sampleRecommendedOrganizations.length + 1) * 500}ms` }} className="animate-fadeInAndFall opacity-0">Back</Button>
      </>
    }

  </div>
}
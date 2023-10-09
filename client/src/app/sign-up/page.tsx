'use client'
import { Button, Card, CardBody, CardFooter, CardHeader, Divider, Input, Select, SelectItem } from "@nextui-org/react";
import { useState } from "react";
import { collegeMajors, slugify } from "../_data-models/college-majors";
import { useRouter } from "next/navigation";

export default function SignUp() {
  type EnrollmentStatus = "undergraduate" | "graduate"
  const [enrollmentStatus, setEnrollmentStatus] = useState<EnrollmentStatus | null>(null);
  type Year = "freshman" | "sophomore" | "junior" | "senior"
  const [year, setYear] = useState<Year | null>(null);
  const [major, setMajor] = useState<string | null>(null);
  const [signUpButtonLoading, setSignUpButtonLoading] = useState<boolean>(false);
  const router = useRouter()

  const handleSignUpClicked = () => {
    setSignUpButtonLoading(true);
    router.push('/home');
  }

  return <div className="flex flex-col items-center pt-12">
    <Card className="w-96">
      <CardHeader className="text-center">
        Sign Up
      </CardHeader>
      <Divider />
      <CardBody className="flex gap-4">
        <Input width="100%" placeholder="First Name" />
        <Input width="100%" placeholder="Last Name" />
        <Input width="100%" type="email" placeholder="Email" />
        <Input width="100%" type="password" placeholder="Password" />
        <Select onChange={(e) => setEnrollmentStatus(e.target.value as EnrollmentStatus)} label="Enrollment Status">
          <SelectItem key="undergraduate" value="undergraduate">
            Undergraduate Student
          </SelectItem>
          <SelectItem key="graduate" value="graduate">
            Graduate Student
          </SelectItem>
        </Select>
        {
          enrollmentStatus == 'undergraduate' ? <Select onChange={(e) => setYear(e.target.value as Year)} label="Year">
            <SelectItem key="freshman" value="freshman">
              Freshman
            </SelectItem>
            <SelectItem key="sophomore" value="sophomore">
              Sophomore
            </SelectItem>

            <SelectItem key="junior" value="junior">
              Junior
            </SelectItem>

            <SelectItem key="senior" value="senior">
              Senior
            </SelectItem>
          </Select> : null
        }
        <Select onChange={(e) => setMajor(e.target.value)} label="Major">
          {
            collegeMajors.map((major) =>
              <SelectItem key={slugify(major)} value={slugify(major)}>{major}</SelectItem>
            )
          }
        </Select>
        <Button onClick={handleSignUpClicked} isLoading={signUpButtonLoading}>
          Sign Up
        </Button>
      </CardBody>
    </Card>
  </div>
}
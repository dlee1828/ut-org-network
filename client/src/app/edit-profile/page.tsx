'use client'

import { Button, Input, Select, SelectItem } from "@nextui-org/react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { collegeMajors, slugify } from "../_data-models/college-majors";
import { Autocomplete, TextField } from "@mui/material";
import { allOrganizations } from "../_data-models/all-organizations";

const data = ["apple", "banana", "cherry"]

const CurrentOrganizationsComponent = () => {
  return <div className="w-96">
    <Autocomplete
      multiple
      id="tags-standard"
      options={allOrganizations}
      renderInput={(params) => (
        <TextField
          {...params}
          variant="standard"
          label="Multiple values"
          placeholder="Favorites"
        />
      )}
    />
  </div>
}

export default function EditProfile() {
  const router = useRouter();
  type EnrollmentStatus = "undergraduate" | "graduate"
  const [enrollmentStatus, setEnrollmentStatus] = useState<EnrollmentStatus | "">("undergraduate");
  type Year = "freshman" | "sophomore" | "junior" | "senior"
  const [firstName, setFirstName] = useState<string>("Daniel");
  const [lastName, setLastName] = useState<string>("Lee");
  const [email, setEmail] = useState<string>("daniel8lee58@gmail.com");
  const [year, setYear] = useState<Year | "">("senior");
  const [major, setMajor] = useState<string | "">("electrical-engineering");

  return <div className="flex flex-col items-center pt-28 gap-4 w-96 mx-auto">
    <Input value={firstName} onChange={(e) => setFirstName(e.target.value)} width="100%" label="First Name" />
    <Input value={lastName} onChange={(e) => setLastName(e.target.value)} width="100%" label="Last Name" />
    <Input value={email} onChange={(e) => setEmail(e.target.value)} width="100%" type="email" label="Email" />
    <Select value={enrollmentStatus} defaultSelectedKeys={[enrollmentStatus]} onChange={(e) => setEnrollmentStatus(e.target.value as EnrollmentStatus)} label="Enrollment Status">
      <SelectItem key="undergraduate" value="undergraduate">
        Undergraduate Student
      </SelectItem>
      <SelectItem key="graduate" value="graduate">
        Graduate Student
      </SelectItem>
    </Select>
    {
      enrollmentStatus == 'undergraduate' ?
        <Select defaultSelectedKeys={[year]} value={year} onChange={(e) => setYear(e.target.value as Year)} label="Year">
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
    <Select defaultSelectedKeys={[major]} value={major} onChange={(e) => setMajor(e.target.value)} label="Major">
      {
        collegeMajors.map((major) =>
          <SelectItem key={slugify(major)} value={slugify(major)}>{major}</SelectItem>
        )
      }
    </Select>
    <CurrentOrganizationsComponent></CurrentOrganizationsComponent>

    <Button onClick={() => router.push('/home')} color="primary" radius="full">Back</Button>
  </div>
}
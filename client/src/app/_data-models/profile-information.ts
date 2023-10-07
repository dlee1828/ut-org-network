type ProfileInformation = {
  firstName: string,
  lastName: string,
  email: string,
  enrollmentStatus: "undergraduate" | "graduate",
  year: "freshman" | "sophomore" | "junior" | "senior" | null,
  major: string,
  interests: string[],
  currentOrganizations: string[]
}
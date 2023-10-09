import { Card, CardBody, CardHeader, HTMLNextUIProps, Image } from "@nextui-org/react";
import { data } from "autoprefixer";

export type RecommendedOrganizationData = {
  name: string;
  description: string;
  image: string;
}

export default function RecommendedOrganization(props: { data: RecommendedOrganizationData } & HTMLNextUIProps) {
  const data = props.data;
  const style = props.style;
  return <Card style={style} isPressable isHoverable className="py-4 animate-fadeInAndFall opacity-0">
    <CardHeader className="pb-0 pt-2 px-4 flex-col items-start">
      {/* <p className="text-tiny uppercase font-bold">Daily Mix</p>
      <small className="text-default-500">12 Tracks</small> */}
      <h4 className="font-bold text-large">{data.name}</h4>
    </CardHeader>
    <CardBody className="overflow-visible py-2 flex flex-row gap-4">
      <Image
        alt="Card background"
        className="object-cover rounded-xl object-fill w-28"
        src={data.image}
      // width={120}
      />
      <span className="h-32 w-96 overflow-scroll">
        {data.description}
      </span>
    </CardBody>
  </Card>
}
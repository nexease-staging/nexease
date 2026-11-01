import WorkforceHub from '@/features/business/workforce-hub';
export default async function Page({params}:{params:Promise<{section:string}>}){const {section}=await params;return <WorkforceHub key={section} section={section}/>}
export function generateStaticParams(){return ['employees','sites','assignments','timesheets','leave','advances','inputs','attendance','payruns','payslips','billing','accounts','settings','reports'].map(section=>({section}));}

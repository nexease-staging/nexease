import WorkforceHub from '@/features/business/workforce-hub';
export default async function Page({params}:{params:Promise<{section:string}>}){const {section}=await params;return <WorkforceHub key={section} section={section}/>}

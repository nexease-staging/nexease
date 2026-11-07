import {render,screen} from "@testing-library/react";
import {describe,it,expect,vi,beforeEach} from "vitest";
import BusinessSetupCard from "./business-setup-card";
const data=vi.hoisted(()=>({setup:{logo:false,email:false,bank:false},permissions:["organizations.update"] as string[]}));
vi.mock("@/features/auth/auth-context",()=>({useAuth:()=>({authentication:{organization:{id:"org"},user:{id:"user"},role:{permissions:data.permissions}}})}));
vi.mock("@/features/business/workspace",()=>({getConfig:vi.fn()}));
vi.mock("@tanstack/react-query",()=>({useQuery:()=>({data:{setup:data.setup},isPending:false,isError:false})}));
beforeEach(()=>{data.setup={logo:false,email:false,bank:false};data.permissions=["organizations.update"]});
describe("Business setup prompts",()=>{
 it("shows all unfinished tasks",()=>{render(<BusinessSetupCard/>);expect(screen.getByRole("link",{name:"Invoice settings"})).toBeVisible();expect(screen.getByRole("link",{name:"Email settings"})).toBeVisible();expect(screen.getByRole("link",{name:"Bank details"})).toBeVisible()});
 it("hides completed tasks individually",()=>{data.setup.logo=true;data.setup.email=true;render(<BusinessSetupCard/>);expect(screen.queryByRole("link",{name:"Invoice settings"})).not.toBeInTheDocument();expect(screen.queryByRole("link",{name:"Email settings"})).not.toBeInTheDocument();expect(screen.getByRole("link",{name:"Bank details"})).toBeVisible()});
 it("removes the whole panel when everything is set up",()=>{data.setup={logo:true,email:true,bank:true};render(<BusinessSetupCard/>);expect(screen.queryByRole("region",{name:"Business setup shortcuts"})).not.toBeInTheDocument();expect(screen.queryByText("Complete your business profile")).not.toBeInTheDocument()});
 it("does not offer organisation settings without permission",()=>{data.permissions=[];render(<BusinessSetupCard/>);expect(screen.queryByRole("link",{name:"Bank details"})).not.toBeInTheDocument();expect(screen.getByRole("link",{name:"Email settings"})).toBeVisible()});
});

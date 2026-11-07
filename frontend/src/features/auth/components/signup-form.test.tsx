import {fireEvent,render,screen,waitFor} from "@testing-library/react";
import {beforeEach,describe,expect,it,vi} from "vitest";
import SignupForm from "./signup-form";
import {signup} from "@/features/auth/api";
const {push}=vi.hoisted(()=>({push:vi.fn()}));
vi.mock("next/navigation",()=>({useRouter:()=>({push})}));
vi.mock("@/features/auth/api",()=>({signup:vi.fn()}));
beforeEach(()=>{vi.clearAllMocks();vi.mocked(signup).mockResolvedValue({} as never)});
describe("Business signup",()=>{
 it("retains business address and admin credentials when creating the account",async()=>{
  render(<SignupForm/>);
  const fields:Record<string,string>={"Company name *":"Demo business","Organisation email *":"office@example.com","Business address":"Pune, Maharashtra 411001","First name *":"Demo","Last name *":"Admin","Login email *":"admin@example.com","Password *":"Valid-demo-password!","Confirm password *":"Valid-demo-password!"};
  Object.entries(fields).forEach(([label,value])=>fireEvent.change(screen.getByLabelText(label,{exact:true}),{target:{value}}));
  fireEvent.click(screen.getByRole("button",{name:"Create organisation"}));
  await waitFor(()=>expect(signup).toHaveBeenCalledWith(expect.objectContaining({address:"Pune, Maharashtra 411001",organization_name:"Demo business",email:"admin@example.com"})));
  expect(push).toHaveBeenCalledWith("/login?signup=success");
 });
 it("does not submit mismatched passwords",async()=>{
  render(<SignupForm/>);
  fireEvent.change(screen.getByLabelText("Password *",{exact:true}),{target:{value:"Valid-password!"}});
  fireEvent.change(screen.getByLabelText("Confirm password *",{exact:true}),{target:{value:"Different-password!"}});
  fireEvent.click(screen.getByRole("button",{name:"Create organisation"}));
  await waitFor(()=>expect(screen.getByText("Passwords do not match.")).toBeInTheDocument());
  expect(signup).not.toHaveBeenCalled();
 });
});

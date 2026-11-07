import {fireEvent,render,screen} from "@testing-library/react";
import {beforeEach,describe,expect,it,vi} from "vitest";
import ModuleNavigation from "./module-navigation";
const state=vi.hoisted(()=>({permissions:["products.read","inventory.read","invoices.read","sales_orders.read"],einvoice:false}));
vi.mock("next/navigation",()=>({usePathname:()=>"/invoices"}));
vi.mock("@/features/auth/auth-context",()=>({useAuth:()=>({authentication:{role:{permissions:state.permissions}}})}));
vi.mock("@/features/business/workspace",()=>({getConfig:vi.fn()}));
vi.mock("@tanstack/react-query",()=>({useQuery:()=>({data:{profile:{modules:["Sales","Inventory","Purchasing"]},modules:{einvoice:state.einvoice}}})}));
beforeEach(()=>{state.permissions=["products.read","inventory.read","invoices.read","sales_orders.read"];state.einvoice=false});
describe("Business module navigation",()=>{
 it("keeps sales routes accessible but hides Pro-only GST documents",()=>{
  render(<ModuleNavigation/>);
  fireEvent.click(screen.getByRole("button",{name:"Sales"}));
  expect(screen.getByRole("link",{name:"Invoices"})).toHaveAttribute("href","/invoices");
  expect(screen.queryByRole("link",{name:"E-Invoices"})).not.toBeInTheDocument();
 });
 it("closes the previous menu and supports Escape",()=>{
  render(<ModuleNavigation/>);
  const sales=screen.getByRole("button",{name:"Sales"}),inventory=screen.getByRole("button",{name:"Inventory"});
  fireEvent.click(sales);fireEvent.click(inventory);
  expect(sales).toHaveAttribute("aria-expanded","false");
  expect(inventory).toHaveAttribute("aria-expanded","true");
  fireEvent.keyDown(document,{key:"Escape"});
  expect(inventory).toHaveAttribute("aria-expanded","false");
 });
 it("shows GST document routes only when enabled and excludes forbidden products",()=>{
  state.einvoice=true;state.permissions=["invoices.read"];
  render(<ModuleNavigation/>);
  expect(screen.queryByRole("button",{name:"Inventory"})).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button",{name:"Sales"}));
  expect(screen.getByRole("link",{name:"E-Invoices"})).toHaveAttribute("href","/e-invoices");
 });
});

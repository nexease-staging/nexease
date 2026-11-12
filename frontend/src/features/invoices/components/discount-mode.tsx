import type {DiscountLine} from '../discount';
export default function DiscountMode({value,onChange,label}:{value:DiscountLine["discount_mode"];onChange:(value:"amount"|"percent")=>void;label:string}){
 return <span role="group" aria-label={label} className="nx-discount-toggle">{(["amount","percent"] as const).map(mode=><button key={mode} type="button" aria-pressed={(value??"amount")===mode} aria-label={mode==="amount"?"Discount in rupees":"Discount in percent"} onClick={()=>onChange(mode)}>{mode==="amount"?"₹":"%"}</button>)}</span>;
}

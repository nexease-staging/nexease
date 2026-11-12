export type DiscountLine={quantity:string;unit_price:string;discount:string;discount_mode?:"amount"|"percent"};
function decimal(value:string):[bigint,bigint] {
 const text=value.trim()||"0";
 if(!/^\d+(\.\d{0,8})?$/.test(text))throw new Error("Enter a valid non-negative discount, quantity and rate (up to 8 decimals).");
 const [whole,fraction=""]=text.split(".");
 return [BigInt(whole+fraction),BigInt(10)**BigInt(fraction.length)];
}
const round=(n:bigint,d:bigint)=>(n+d/BigInt(2))/d;
export function discountAmount(line:DiscountLine):string {
 const [q,qs]=decimal(line.quantity),[p,ps]=decimal(line.unit_price),[v,vs]=decimal(line.discount);
 const base=round(q*p*BigInt(100),qs*ps);
 if(line.discount_mode==="percent"&&v>BigInt(100)*vs)throw new Error("Discount percentage must be between 0 and 100.");
 const cents=line.discount_mode==="percent"?round(base*v,vs*BigInt(100)):round(v*BigInt(100),vs);
 if(cents>base)throw new Error("Discount cannot exceed the line value.");
 return (cents/BigInt(100)).toString()+"."+(cents%BigInt(100)).toString().padStart(2,"0");
}
export function previewDiscount(line:DiscountLine):number {
 try{return Number(discountAmount(line));}catch{return 0;}
}
export function discountedPayload<T extends DiscountLine>(line:T) {
 const {discount_mode,...fields}=line;
 void discount_mode;
 return {...fields,discount:discountAmount(line)};
}

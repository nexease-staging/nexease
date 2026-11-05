export type Plan={code:string;name:string;price:number;limits:Record<string,number>;features:string[];published:boolean;annual_price?:number;annual_published?:boolean};
export type Membership={plan:string;cycle?:string;status:string;start:string;end:string;suspended:boolean;limits:Record<string,number>;features:string[];subscription_id:string};
export type Catalog={plans:Plan[];payments_enabled:boolean;price_note:string;terms_url:string;privacy_url:string;refund_url:string};
export const featureLabels:Record<string,string>={users:'Active users',invoices:'Issued invoices / month',bills:'Posted bills / month',products:'Products',warehouses:'Active warehouses',employees:'Active employees',ai:'AI chats / month',scan_pages:'Scan pages / month'};

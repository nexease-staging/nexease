export interface Quotation {
  number: string;
  customer: string;
  customer_details?: Record<string,string>;
  date: string;
  valid_until: string;
  notes: string;
  total: string;
  conversion?: {kind:"order"|"invoice"; status:string; id?:string; number?:string};
  linked_invoice?: {id:string; number:string};
  items: {name:string; quantity:string; unit_price:string; tax_rate:string; discount:string; total:string;
    product_id?:string; sku?:string; unit?:string; item_type?:string; hsn_code?:string}[];
}

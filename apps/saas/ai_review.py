"""Prompt contract and lossless review normalization for supported entry kinds."""
FIELD_GUIDE={
 'category':{'name':'Category name (not the category field)','description':'Full description provided by the user'},
 'product':{'name':'Product/service name','category':'Existing category name, resolved server-side','category_id':'Only a supplied ID','sku':'Supplied SKU only','selling_price':'Selling rate','cost_price':'Cost only when supplied','unit':'Unit','item_type':'goods or service','hsn_code':'HSN/SAC only when supplied'},
 'invoice':{'party_name':'Customer name','party_code':'Customer code only if supplied','party_address':'Customer billing address','party_gstin':'Customer GSTIN','party_state':'Customer state','date':'Invoice date','due_date':'Due date','number':'Invoice number if supplied','supply_type':'taxable/exempt/nil_rated/non_gst/unregistered','place_of_supply':'Two-digit state code if supplied','po_number':'Purchase order reference','notes':'All additional invoice instructions/details'},
 'bill':{'party_name':'Supplier name','date':'Bill date','number':'Supplier bill number'},
 'purchase_order':{'party_name':'Supplier name','date':'Order date','number':'PO number if provided'},
 'employee':{'name':'Employee name','rate':'Salary or rate','basis':'monthly/daily/hourly/piece'},
 'site':{'name':'Site name','address':'Site address'},
 'expense':{'party_name':'Paid to','description':'Purpose','amount':'Amount','date':'Expense date','category':'Expense category','payment_mode':'Payment mode'},
 'advance':{'employee_name':'Employee name','amount':'Amount','date':'Advance date'},
 'assignment':{'employee_name':'Employee name','site_name':'Site name'},
 'timesheet':{'employee_name':'Employee name','site_name':'Site name','date':'Work date','hours':'Hours'},
 'attendance':{'employee_name':'Employee name','month':'YYYY-MM','paid_days':'Paid days'},
 'leave_request':{'employee_name':'Employee name','start_date':'Start','end_date':'End','leave_type':'Type'},
}

def prompt_guide():
 import json
 return ''' Populate the review form, not an instruction to open a screen. Preserve EVERY explicitly provided value in its corresponding field. The same word can mean different fields by kind: category creation uses fields.name; invoices use fields.party_name and items[].name. Never return an empty form when the user supplied details. If one required value is missing, still populate all known values and ask only for missing details. Keep separate invoice lines for each supplied item. A later message correcting a previous proposal changes only the specified values; preserve the rest unless the user starts a different entry. Do not copy previous values into a clearly different kind. Preserve currency amounts without symbols, quantities, discounts, dates, contact details and notes. Put otherwise unmapped relevant details in notes (or category/product description). Do not invent IDs or tax treatment. Exact master names are resolved by the application; ask for names rather than internal IDs. One business entry per proposal; if multiple distinct entries are requested ask which to prepare first. Field mapping: '''+json.dumps(FIELD_GUIDE)+''' Examples: "Create category Safety Equipment, description Helmets and gloves" => kind category, fields.name Safety Equipment, fields.description Helmets and gloves. "Invoice Acme for 3 helmets at 500 each, GST 18%, no discount" => kind invoice, fields.party_name Acme, fields.supply_type taxable, items [{name:Helmets, quantity:3, unit_price:500, tax_rate:18, discount:0}]; missing date/place of supply remain questions. Never claim records have been saved before confirmation.'''

def normalize_review(data):
 f=data['fields'];kind=data['kind']
 if kind=='category' and not f.get('name') and f.get('category'):f['name']=f['category']
 if kind in ('invoice','bill','purchase_order') and not f.get('party_name') and f.get('name'):f['party_name']=f['name']
 if kind in ('invoice','bill','purchase_order'):
  for line in data['items']:
   if not line.get('item_type'):line['item_type']='goods'
   if f.get('supply_type') in ('unregistered','exempt','nil_rated','non_gst') and not line.get('tax_rate'):
    line['tax_rate']='0'
    data['warnings'].append('Zero tax applied from the selected GST treatment; review before saving.')
 return data

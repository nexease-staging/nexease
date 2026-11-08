"""Local, escaped print layouts. No provider data or remote image requests."""
from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


def money(value): return f'{Decimal(str(value or 0)):,.2f}'


def amount_words(value):
    value=Decimal(str(value)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    small='Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen'.split()
    tens='Zero Ten Twenty Thirty Forty Fifty Sixty Seventy Eighty Ninety'.split()
    def words(n):
        if n<20:return small[n]
        if n<100:return tens[n//10]+(' '+small[n%10] if n%10 else '')
        for scale,label in ((10000000,'Crore'),(100000,'Lakh'),(1000,'Thousand'),(100,'Hundred')):
            if n>=scale:return words(n//scale)+' '+label+(' '+words(n%scale) if n%scale else '')
    rupees=int(abs(value));paise=int((abs(value)-rupees)*100)
    return ('Minus ' if value<0 else '')+words(rupees)+' Rupees'+(' and '+words(paise)+' Paise' if paise else '')+' Only'


def retail_invoice(invoice, branding):
    from .print_documents import document_styles
    from .billing import tax_heads
    from apps.finance.documents.branding import logo_story
    from reportlab.graphics.barcode.qr import QrCodeWidget
    from reportlab.graphics.shapes import Drawing
    org=invoice.organization;d=invoice.billing_details or {};buf=BytesIO();styles=document_styles()
    accent=colors.HexColor(branding.get('accent_color') or ('#176fa3' if d.get('template')=='retail_blue' else '#006b58'))
    light=colors.Color(.93+.07*accent.red,.93+.07*accent.green,.93+.07*accent.blue)
    styles.add(ParagraphStyle('RetailCell',fontName='NX',fontSize=8,leading=11,wordWrap='CJK'))
    styles.add(ParagraphStyle('RetailHead',fontName='NX-Bold',fontSize=7,leading=9,wordWrap='CJK'))
    styles.add(ParagraphStyle('RetailBrand',fontName='NX-Bold',fontSize=21,leading=25,textColor=accent))
    def p(value,style='RetailCell'):return Paragraph(escape(str(value or '')).replace('\n','<br/>'),styles[style])
    def table(rows,widths,header=False):
        result=Table([[p(c,'RetailHead' if header and ri==0 else 'RetailCell') for c in row] for ri,row in enumerate(rows)],colWidths=widths,repeatRows=1 if header else 0)
        result.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.5,accent),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]+([('BACKGROUND',(0,0),(-1,0),light)] if header else [])))
        return result
    story=logo_story(branding)+[p(org.name,'RetailBrand'),p(org.address),p('Phone: '+(org.phone or '')+'   Email: '+(org.email or '')),Spacer(1,12)]
    title='TAX INVOICE' if d.get('supply_type')=='taxable' else 'BILL OF SUPPLY' if d.get('supply_type') in ('exempt','nil_rated','non_gst') else 'INVOICE'
    story += [table([['GSTIN: '+d.get('supplier_gstin','Not configured'),title,'ORIGINAL FOR RECIPIENT']],[210,150,175],True)]
    story += [table([['Customer details','Invoice details'],[invoice.billing_name+'\n'+invoice.billing_address+'\nGSTIN: '+(invoice.customer_gstin or 'Unregistered')+'\nPlace of supply: '+d.get('place_of_supply',''), 'Invoice: '+invoice.invoice_number+'\nDate: '+invoice.invoice_date.strftime('%d-%b-%Y')+'\nDue: '+(invoice.due_date.strftime('%d-%b-%Y') if invoice.due_date else '-')+'\nPO: '+d.get('po_number','')],[ 'Ship to / service address',d.get('shipping_address') or invoice.billing_address]],[267,268]),Spacer(1,12)]
    irp=getattr(invoice,'einvoice',{}) or {}
    if irp.get('status')=='registered' and irp.get('environment')=='live':
        qr=QrCodeWidget(irp['qr']);x,y,w,h=qr.getBounds();scale=95/(w-x)
        drawing=Drawing(95,95,transform=[scale,0,0,scale,-x*scale,-y*scale]);drawing.add(qr)
        block=Table([[p('IRN: '+irp['irn']+'\nAcknowledgment: '+irp.get('ack_no','')+' '+irp.get('ack_date','')),drawing]],colWidths=[430,105]);story += [block,Spacer(1,10)]
    elif irp.get('status'):story += [p('IRP: '+irp['status']+(' (TEST ONLY)' if irp.get('environment')!='live' else '')),Spacer(1,8)]
    rows=[['Sr.','Product / service','HSN /\nSAC','Qty /\nunit','Rate','Taxable','GST %','Tax','Total']]
    for n,item in enumerate(invoice.items,1):
        name=item.item_name or (item.product.name if item.product else '')
        if item.show_description and item.description:name+='\n'+item.description
        rows.append([n,name,item.hsn_code,str(item.quantity)+' '+(item.unit or ''),money(item.unit_price),money(item.line_subtotal-item.discount),str(item.tax_rate),money(item.line_tax),money(item.line_total)])
    story += [table(rows,[25,140,45,48,52,60,35,55,75],True),Spacer(1,12)]
    cg,sg,ig=tax_heads(invoice)
    totals=[['Taxable amount',money(invoice.total_amount-invoice.tax_amount)]]
    totals+= [['CGST',money(cg)],['SGST / UTGST',money(sg)],['IGST',money(ig)]] if d.get('tax_reviewed') else [['Tax - classification pending',money(invoice.tax_amount)]]
    totals += [['Total '+(org.currency or 'INR'),money(invoice.total_amount)],['Paid',money(invoice.amount_paid)],['Balance due',money(invoice.balance_due)]]
    details='Amount in words\n'+(amount_words(invoice.total_amount) if (org.currency or 'INR')=='INR' else str(invoice.total_amount)+' '+org.currency)+'\n\nBank details\n'+d.get('bank_details',branding.get('bank_details',''))+'\n\nTerms & conditions\n'+d.get('terms',branding.get('terms',''))
    summary=Table([[p(details),table(totals,[145,93])]],colWidths=[285,250]);summary.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),.5,accent)]));story += [summary,Spacer(1,14)]
    if invoice.notes:story += [p('Notes: '+invoice.notes),Spacer(1,10)]
    story += [table([['For '+org.name,'Authorised signatory'],['',d.get('signatory',branding.get('signatory',''))]],[285,250])]
    def footer(c,doc):
        c.setFont('NX',8);c.setFillColor(accent);c.drawString(30,20,'Generated with NexEase');c.drawRightString(565,20,'Page '+str(doc.page))
    SimpleDocTemplate(buf,pagesize=A4,leftMargin=30,rightMargin=30,topMargin=26,bottomMargin=35,title=title+' '+invoice.invoice_number).build(story,onFirstPage=footer,onLaterPages=footer)
    return buf.getvalue()


def salary_slip(org,run,row,branding):
    from .print_documents import document_styles
    from apps.finance.documents.branding import logo_story
    buf=BytesIO();styles=document_styles();accent=colors.HexColor(branding.get('accent_color') or '#006b58')
    def p(v):return Paragraph(escape(str(v or '')).replace('\n','<br/>'),styles['Normal'])
    def table(rows,widths):
        result=Table([[p(v) for v in r] for r in rows],colWidths=widths,repeatRows=1)
        result.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7f3ef')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#cedbd6')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]));return result
    employee=row['employee'];result=row['result'];inputs=row.get('inputs',{})
    story=logo_story(branding)+[Paragraph(escape(org.name),styles['Title']),p(org.address),Spacer(1,12),Paragraph('SALARY SLIP',styles['Heading1']),table([['Employee','Payroll period'],[employee.get('name',''),run.key],['Employee code: '+employee.get('code',''),'Status: '+run.data['status']]],[260,260]),Spacer(1,16)]
    earnings=[('Basic / earned pay',result.get('base','0')),('Overtime',result.get('overtime','0')),('Allowances / additions',result.get('additions','0'))]
    deductions=[('Employee PF',result.get('pf','0')),('Employee ESI',result.get('esi','0'))]+[(label,inputs.get(key,'0')) for key,label in [('tds','TDS'),('professional_tax','Professional tax'),('lwf','LWF'),('advance_recovery','Advance recovery'),('other_deductions','Other deductions')]]
    rows=[['Earnings','Amount','Deductions','Amount']]
    for i in range(max(len(earnings),len(deductions))):
        a=earnings[i] if i<len(earnings) else ('','');b=deductions[i] if i<len(deductions) else ('','');rows.append([a[0],money(a[1]) if a[1]!='' else '',b[0],money(b[1]) if b[1]!='' else ''])
    rows.append(['Gross earnings',money(result.get('gross','0')),'Total deductions',money(result.get('deductions','0'))])
    story += [table(rows,[175,85,175,85]),Spacer(1,16),table([['NET PAY (INR)',money(result.get('net','0'))]],[350,170]),Spacer(1,10),p(amount_words(result.get('net','0'))),Spacer(1,20),p('Employer contributions (not employee deductions): PF '+money(result.get('employer_pf','0'))+'; ESI '+money(result.get('employer_esi','0'))),p('Payment is recorded separately. Payroll reference: '+str(run.id))]
    SimpleDocTemplate(buf,pagesize=A4,leftMargin=35,rightMargin=35,title='Salary slip '+run.key).build(story)
    return buf.getvalue()

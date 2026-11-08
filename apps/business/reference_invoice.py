"""Reference-style A4 retail invoice. Preview and download use these same bytes."""
from io import BytesIO
from decimal import Decimal
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image


def indian_money(value):
    text=f'{Decimal(str(value or 0)):,.2f}'
    whole,frac=text.replace(',','').split('.')
    sign='-' if whole.startswith('-') else '';whole=whole.lstrip('-')
    tail=whole[-3:];head=whole[:-3];parts=[]
    while head:parts.insert(0,head[-2:]);head=head[:-2]
    return sign+(','.join(parts+[tail]))+'.'+frac


def reference_invoice(invoice, branding):
    from .print_documents import document_styles
    from .professional_documents import amount_words
    from .billing import tax_heads
    document_styles()  # Registers the bundled Unicode fonts.
    d=invoice.billing_details or {};org=invoice.organization;buf=BytesIO();width=535
    accent=colors.HexColor(branding.get('accent_color') or ('#1976ad' if d.get('template')=='retail_blue' else '#006b58'))
    light=colors.Color(.90+.10*accent.red,.94+.06*accent.green,.98+.02*accent.blue)
    normal=ParagraphStyle('ReferenceCell',fontName='NX',fontSize=7.7,leading=10)
    bold=ParagraphStyle('ReferenceBold',parent=normal,fontName='NX-Bold')
    numeric=ParagraphStyle('ReferenceNumber',parent=normal,fontSize=6.2,leading=8,alignment=2)
    numeric_bold=ParagraphStyle('ReferenceNumberBold',parent=numeric,fontName='NX-Bold')
    center=ParagraphStyle('ReferenceCenter',parent=bold,alignment=1,fontSize=6.5,leading=8)
    brand=ParagraphStyle('ReferenceBrand',parent=bold,fontSize=21,leading=25,textColor=accent)
    def p(value,style=normal):return Paragraph(escape(str(value if value is not None else '')).replace('\n','<br/>'),style)
    def grid(rows,widths,heights=None,extra=()):
        t=Table(rows,colWidths=widths,rowHeights=heights,hAlign='LEFT')
        t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.6,accent),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]+list(extra)))
        return t
    logo=''
    if branding.get('logo'):
        import base64
        try:
            logo=Image(BytesIO(base64.b64decode(branding['logo'].split(',',1)[1],validate=True)))
            logo._restrictSize(66,61)
        except (ValueError,OSError):logo=''
    identity=[p(org.name,brand),p(org.address),p('Ph: '+(org.phone or '')+('   '+org.email if org.email else ''))]
    header=Table([[logo,identity]],colWidths=[76,459],hAlign='LEFT');header.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LINEBELOW',(0,0),(-1,-1),1.2,colors.black),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    story=[header,Spacer(1,8)]
    title='TAX INVOICE' if d.get('supply_type')=='taxable' else 'BILL OF SUPPLY' if d.get('supply_type') in ('exempt','nil_rated','non_gst') else 'INVOICE'
    story.append(grid([[p('GSTIN: '+(d.get('supplier_gstin') or '-'),bold),p(title,ParagraphStyle('Title',parent=center,fontSize=14,leading=18,textColor=accent)),p('ORIGINAL FOR RECIPIENT',center)]],[210,165,160],extra=[('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    customer=[p('Customer Detail',center),p('Name      '+invoice.billing_name,bold),p('Address   '+invoice.billing_address),p('GSTIN      '+(invoice.customer_gstin or '-')),p('Place of supply   '+d.get('place_of_supply','-'))]
    details=[p('Invoice No.   '+invoice.invoice_number+'                Invoice Date   '+invoice.invoice_date.strftime('%d-%b-%Y'),bold)]
    for label,key in [('PO No.','po_number'),('PO date','po_date'),('Site / project','site_name'),('Service from','service_from'),('Service to','service_to'),('Ship to','shipping_address'),('Payment terms','payment_terms')]:
        if d.get(key):details.append(p(label+': '+d[key]))
    if invoice.due_date:details.append(p('Due date: '+invoice.due_date.strftime('%d-%b-%Y')))
    story += [grid([[customer,details]],[215,320],heights=[max(88,30+len(details)*12)]),Spacer(1,12)]
    irp=getattr(invoice,'einvoice',{}) or {}
    if irp.get('status')=='registered' and irp.get('environment')=='live':
        from reportlab.graphics.barcode.qr import QrCodeWidget
        from reportlab.graphics.shapes import Drawing
        qr=QrCodeWidget(irp['qr']);x,y,w,h=qr.getBounds();scale=65/(w-x)
        drawing=Drawing(65,65,transform=[scale,0,0,scale,-x*scale,-y*scale]);drawing.add(qr)
        story.append(grid([[p('IRN: '+irp['irn']+'\nAcknowledgment: '+irp.get('ack_no','')+' '+irp.get('ack_date','')),drawing]],[460,75]))
    elif irp.get('status'):story.append(p('IRP: '+irp['status']+(' (TEST ONLY)' if irp.get('environment')!='live' else '')))
    reviewed=d.get('tax_reviewed');taxable=d.get('supply_type')=='taxable'
    intra=reviewed and taxable and d.get('supplier_state')==d.get('place_of_supply')
    heads=['CGST','SGST / UTGST'] if intra else ['IGST' if reviewed and taxable else 'Tax']
    widths=([24,126,35,33,48,69,17,47,17,47,72] if intra else [21,144,47,43,56,70,27,53,74])
    # Normalize to exactly the invoice frame width.
    widths=[v*width/sum(widths) for v in widths]
    labels=['Sr.\nNo.','Name of Product / Service','HSN / SAC','Qty','Rate','Taxable Value']
    top=[p(v,center) for v in labels]
    second=['']*6
    for h in heads:top += [p(h,center),''];second += [p('%',center),p('Amount',center)]
    top += [p('Total',center)];second += ['']
    rows=[top,second];commands=[('BACKGROUND',(0,0),(-1,1),light)]
    for col in list(range(6))+[len(widths)-1]:commands.append(('SPAN',(col,0),(col,1)))
    for col in range(6,len(widths)-1,2):commands.append(('SPAN',(col,0),(col+1,0)))
    heights=[16,14]
    for n,item in enumerate(invoice.items,1):
        name=item.item_name or (item.product.name if item.product else '')
        description=item.description if item.show_description else ''
        desc=[p(name,bold)]+([p(description)] if description else [])
        row=[p(n),desc,p(item.hsn_code),p(str(item.quantity)+' '+(item.unit or '')),p(indian_money(item.unit_price),numeric),p(indian_money(item.line_subtotal-item.discount),numeric)]
        tax=Decimal(str(item.line_tax));rate=Decimal(str(item.tax_rate))
        if intra:
            cg=(tax/2).quantize(Decimal('.01'))
            for amount in (cg,tax-cg):row += [p(str(rate/2)),p(indian_money(amount),numeric)]
        else:row += [p(str(rate)),p(indian_money(tax),numeric)]
        row += [p(indian_money(item.line_total),numeric)];rows.append(row);heights.append(None)
    item_table=grid(rows,widths,extra=commands+[('ALIGN',(4,2),(-1,-1),'RIGHT'),('BACKGROUND',(5,2),(5,-1),light),('BACKGROUND',(-1,2),(-1,-1),light),('LINEBELOW',(0,2),(-1,-1),0,colors.white)])
    item_table.repeatRows=2
    # Stretch short invoices to the reference's tall item area without truncating long ones.
    actual=item_table.wrap(width,700)[1]
    if actual<285:
        rows.append(['']*len(widths));heights=[16,14]+[None]*len(invoice.items)+[285-actual]
        item_table=grid(rows,widths,heights,commands+[('BACKGROUND',(5,2),(5,-1),light),('BACKGROUND',(-1,2),(-1,-1),light),('LINEBELOW',(0,2),(-1,-1),0,colors.white)])
        item_table.repeatRows=2
    story.append(item_table)
    cg,sg,ig=tax_heads(invoice)
    total=['']*len(widths);total[1]=p('Total',bold);total[3]=p(sum((Decimal(str(i.quantity)) for i in invoice.items),Decimal(0)),bold);total[5]=p(indian_money(invoice.total_amount-invoice.tax_amount),numeric_bold)
    if intra:total[7]=p(indian_money(cg),numeric_bold);total[9]=p(indian_money(sg),numeric_bold)
    else:total[7]=p(indian_money(invoice.tax_amount),numeric_bold)
    total[-1]=p(indian_money(invoice.total_amount),numeric_bold)
    story += [grid([total],widths,extra=[('BACKGROUND',(0,0),(-1,-1),light)]),Spacer(1,12)]
    words=amount_words(invoice.total_amount) if (org.currency or 'INR')=='INR' else str(invoice.total_amount)+' '+org.currency
    bank=d.get('bank_details') or branding.get('bank_details','')
    terms=d.get('terms') or branding.get('terms','')
    bank_content=p(bank or '-')
    # Only generate a payment QR from an explicitly labelled, saved UPI ID.
    import re
    from urllib.parse import urlencode
    upi=re.search(r'UPI\s*(?:ID)?\s*[:=]\s*([A-Za-z0-9._-]+@[A-Za-z0-9.-]+)',bank,re.I)
    if upi:
        from reportlab.graphics.barcode.qr import QrCodeWidget
        from reportlab.graphics.shapes import Drawing
        payload='upi://pay?'+urlencode({'pa':upi.group(1),'pn':org.name,'cu':'INR'})
        qr=QrCodeWidget(payload);x,y,w,h=qr.getBounds();scale=76/(w-x)
        drawing=Drawing(76,76,transform=[scale,0,0,scale,-x*scale,-y*scale]);drawing.add(qr)
        bank_content=Table([[p(bank),[drawing,p('Pay using UPI',center)]]],colWidths=[220,90])
    bank_height=max(88,bank_content.wrap(310,800)[1]+8) if isinstance(bank_content,Table) else 88
    left=grid([[p('Total in words',center)],[p(words.upper())],[p('Bank Details',center)],[bank_content],[p('Terms and Conditions',center)],[p(terms or '-')]], [320],heights=[16,None,16,bank_height,16,None])
    totals=[[p('Taxable Amount',bold),p(indian_money(invoice.total_amount-invoice.tax_amount),numeric_bold)]]
    if reviewed:
        for label,value in ([('CGST',cg),('SGST / UTGST',sg)] if intra else [('IGST',ig)] if taxable else []):totals.append([p('Add: '+label,bold),p(indian_money(value),bold)])
    else:totals.append([p('Tax - classification pending'),p(indian_money(invoice.tax_amount))])
    totals += [[p('Total Tax',bold),p(indian_money(invoice.tax_amount),numeric_bold)],[p('Total Amount After Tax',bold),p(('₹' if (org.currency or 'INR')=='INR' else org.currency+' ')+indian_money(invoice.total_amount),bold)],[p('Paid / Balance due'),p(indian_money(invoice.amount_paid)+' / '+indian_money(invoice.balance_due))]]
    tt=grid(totals,[128,87],extra=[('BACKGROUND',(0,0),(-1,-1),light)])
    signature=grid([[p('(E & O.E.)',center)],[p('Certified that the particulars given above are true and correct.',center)],[p('For '+org.name,center)],[p(d.get('signatory') or branding.get('signatory',''))],[p('Authorised Signatory',center)]],[215],heights=[16,None,None,72,16])
    right=[tt,signature]
    right_height=tt.wrap(215,800)[1]+signature.wrap(215,800)[1]
    left_height=left.wrap(320,800)[1]
    if right_height>left_height:
        left._argH[3]=bank_height+right_height-left_height
        left._rowHeights[3]=left._argH[3]
    bottom=Table([[left,right]],colWidths=[320,215],hAlign='LEFT');bottom.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    story.append(bottom)
    if invoice.notes:story.append(p('Notes: '+invoice.notes))
    def footer(c,doc):
        c.setFont('NX',7);c.setFillColor(accent);c.drawString(30,18,'Generated with NexEase');c.drawRightString(565,18,'Page '+str(doc.page))
    SimpleDocTemplate(buf,pagesize=A4,leftMargin=30,rightMargin=30,topMargin=25,bottomMargin=30,title=title+' '+invoice.invoice_number).build(story,onFirstPage=footer,onLaterPages=footer)
    return buf.getvalue()

"""Portable, escaped PDF documents with no remote image fetches."""
from io import BytesIO
import base64
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from .billing import TEMPLATES, tax_heads
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('NX',str(Path(__file__).with_name('fonts')/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('NX-Bold',str(Path(__file__).with_name('fonts')/'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('NX',normal='NX',bold='NX-Bold',italic='NX',boldItalic='NX-Bold')
def document_styles():
    styles=getSampleStyleSheet()
    for name in styles.byName:
        styles[name].fontName='NX-Bold' if name.startswith(('Heading','Title')) else 'NX'
    return styles


def invoice_pdf(invoice):
    d=invoice.billing_details or {};org=invoice.organization
    _,name,color,layout=next((t for t in TEMPLATES if t[0]==d.get('template')),TEMPLATES[0])
    accent=colors.HexColor(color);buf=BytesIO();styles=document_styles()
    styles.add(ParagraphStyle(name='Cell',fontName='NX',fontSize=8 if layout!='compact' else 7,leading=11,wordWrap='CJK'))
    styles.add(ParagraphStyle(name='Brand',fontName='NX-Bold',fontSize=21,leading=25,textColor=accent,spaceAfter=8))
    def p(v,style='Cell'):return Paragraph(escape(str('—' if v is None or v=='' else v)).replace('\n','<br/>'),styles[style])
    story=[]
    if d.get('logo'):
        im=Image(BytesIO(base64.b64decode(d['logo'].split(',',1)[1])));im._restrictSize(110,48);im.hAlign='LEFT';story+=[im,Spacer(1,8)]
    title='Tax invoice' if d.get('supply_type')=='taxable' else 'Bill of supply' if d.get('supply_type') in ('exempt','nil_rated','non_gst') else 'Invoice'
    header=Table([[p(org.name,'Brand'),p(title.upper(),'Heading2')],[p(org.address),p(invoice.invoice_number)],[p('GSTIN: '+d.get('supplier_gstin','Not configured')),p('Status: '+invoice.status)]],colWidths=[330,205])
    header.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,-1),(-1,-1),2,accent)]))
    if layout=='banner':header.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f1f5f9')),('BOX',(0,0),(-1,-1),1,accent)]))
    story += [header,Spacer(1,16)]
    meta=[['Invoice date',str(invoice.invoice_date.date()),'Due date',str(invoice.due_date.date()) if invoice.due_date else '—'],['PO number',d.get('po_number',''),'PO date',d.get('po_date','')],['Service period',d.get('service_from','')+' to '+d.get('service_to',''),'Site / project',d.get('site_name','')],['Place of supply',d.get('place_of_supply',''),'Supply classification',d.get('supply_type','Unclassified')]]
    mt=Table([[p(v) for v in r] for r in meta],colWidths=[100,167,100,168]);mt.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(0,-1),colors.HexColor('#f8fafc')),('BACKGROUND',(2,0),(2,-1),colors.HexColor('#f8fafc'))]));story += [mt,Spacer(1,14)]
    party=Table([[p('BILL TO','Heading4'),p('SHIP TO / SERVICE LOCATION','Heading4')],[p(invoice.billing_name+'\n'+invoice.billing_address+'\nGSTIN: '+(invoice.customer_gstin or 'Unregistered')),p(d.get('shipping_address') or d.get('site_name') or invoice.billing_address)]],colWidths=[268,267]);party.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]));story += [party,Spacer(1,14)]
    rows=[['Description / G-S','HSN/SAC','Qty / unit','Rate','Discount','GST %','Amount']]
    for i in invoice.items:
        desc=i.item_name or i.product.name
        if i.show_description and i.description:desc+='\n'+i.description
        desc+='\n'+(i.item_type or i.product.item_type).upper()
        rows.append([desc,i.hsn_code or i.product.hsn_code,str(i.quantity)+' '+(i.unit or i.product.unit),str(i.unit_price),str(i.discount),str(i.tax_rate),str(i.line_total)])
    styles.add(ParagraphStyle(name='TableHead',parent=styles['Cell'],textColor=colors.white,fontName='NX-Bold'))
    table=Table([[p(v,'TableHead' if ri==0 else 'Cell') for v in r] for ri,r in enumerate(rows)],colWidths=[170,55,65,65,60,45,75],repeatRows=1)
    commands=[('BACKGROUND',(0,0),(-1,0),accent),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),4 if layout=='compact' else 8),('BOTTOMPADDING',(0,0),(-1,-1),4 if layout=='compact' else 8)]
    # Header paragraphs use white text independently of body.

    if layout in ('grid','compact'):commands += [('GRID',(0,0),(-1,-1),.3,colors.HexColor('#cbd5e1'))]
    elif layout in ('stripe','banner'):commands += [('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f1f5f9')])]
    else:commands += [('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#e2e8f0'))]
    table.setStyle(TableStyle(commands));story += [table,Spacer(1,16)]
    cg,sg,ig=tax_heads(invoice)
    totals=[['Subtotal',invoice.subtotal],['Discount',invoice.discount_amount]]
    totals += [['CGST',cg],['SGST / UTGST',sg],['IGST',ig]] if d.get('tax_reviewed') else [['Tax (unclassified)',invoice.tax_amount]]
    totals += [['Total '+(org.currency or 'INR'),invoice.total_amount],['Paid',invoice.amount_paid],['Balance due',invoice.balance_due]]
    tt=Table([[p(k),p(v)] for k,v in totals],colWidths=[135,95],hAlign='RIGHT');tt.setStyle(TableStyle([('LINEABOVE',(0,-3),(-1,-3),1,accent),('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#f1f5f9'))]));story += [tt]
    for label,key in [('Payment terms','payment_terms'),('Bank details','bank_details'),('Terms & conditions','terms'),('Authorised signatory','signatory')]:
        if d.get(key):story += [Spacer(1,10),p(label,'Heading4'),p(d[key])]
    if invoice.notes:story += [Spacer(1,10),p('Notes','Heading4'),p(invoice.notes)]
    if not d.get('tax_reviewed'):story += [Spacer(1,10),p('Tax classification pending. Review before GST reporting.')]
    def footer(c,doc):
        c.saveState();c.setFont('NX',8);c.setFillColor(accent);c.drawString(30,22,'NexEase · '+name);c.drawRightString(565,22,'Page '+str(doc.page));c.restoreState()
    SimpleDocTemplate(buf,pagesize=A4,leftMargin=30,rightMargin=30,topMargin=30,bottomMargin=40,title='Invoice '+invoice.invoice_number).build(story,onFirstPage=footer,onLaterPages=footer)
    return buf.getvalue()

def payslip_pdf(org,run,row):
    styles=document_styles();buf=BytesIO()
    def p(v):return Paragraph(escape(str('—' if v is None or v=='' else v)),styles['Normal'])
    story=[p(org.name),Spacer(1,14),Paragraph('Payslip · '+escape(run.key),styles['Title']),p(row['employee'].get('name')),p('Employee code: '+row['employee'].get('code','')),p('Status: '+run.data['status']),Spacer(1,14)]
    rows=[['Component','Amount (INR)']]+[[k.replace('_',' ').title(),v] for k,v in row['result'].items()]
    rows += [[k.replace('_',' ').title(),v] for k,v in row.get('inputs',{}).items() if k in ('tds','professional_tax','lwf','advance_recovery','other_deductions','allowances','bonus','arrears')]
    t=Table([[p(v) for v in r] for r in rows],colWidths=[340,180],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dbeafe')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8fafc')]),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story+=[t,Spacer(1,15),p('Salary payment is recorded separately. Employer contributions are not employee deductions.'),p('Payroll reference: '+str(run.id))]
    from .models import BusinessRecord
    prefs=BusinessRecord.objects(organization=org,kind='workforce_preferences',key='default').first()
    if prefs and prefs.data.get('payslip_footer'):story += [Spacer(1,12),p(prefs.data['payslip_footer'])]
    SimpleDocTemplate(buf,pagesize=A4,title='Payslip '+run.key).build(story)
    return buf.getvalue()

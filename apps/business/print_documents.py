"""Portable, escaped PDF documents with no remote image fetches."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from .billing import settings
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
    """Invoice PDF in the business's chosen template (applies to every invoice and estimate)."""
    from .doc_templates import from_invoice, render_for
    return render_for(invoice.organization, from_invoice(invoice))

def payslip_pdf(org,run,row):
    branding=settings(org)
    if branding.get('payslip_template','professional')=='professional':
        from .professional_documents import salary_slip
        return salary_slip(org,run,row,branding)
    styles=document_styles();buf=BytesIO()
    def p(v):return Paragraph(escape(str('—' if v is None or v=='' else v)),styles['Normal'])
    story=[p(org.name),Spacer(1,14),Paragraph('Payslip · '+escape(run.key),styles['Title']),p(row['employee'].get('name')),p('Employee code: '+row['employee'].get('code','')),p('Status: '+run.data['status']),Spacer(1,14)]
    from apps.finance.documents.branding import logo_story
    story[0:0]=logo_story(settings(org))
    rows=[['Component','Amount (INR)']]+[[k.replace('_',' ').title(),v] for k,v in row['result'].items()]
    rows += [[k.replace('_',' ').title(),v] for k,v in row.get('inputs',{}).items() if k in ('tds','professional_tax','lwf','advance_recovery','other_deductions','allowances','bonus','arrears')]
    t=Table([[p(v) for v in r] for r in rows],colWidths=[340,180],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(settings(org).get('accent_color') or '#dbeafe')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8fafc')]),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story+=[t,Spacer(1,15),p('Salary payment is recorded separately. Employer contributions are not employee deductions.'),p('Payroll reference: '+str(run.id))]
    from .models import BusinessRecord
    prefs=BusinessRecord.objects(organization=org,kind='workforce_preferences',key='default').first()
    if prefs and prefs.data.get('payslip_footer'):story += [Spacer(1,12),p(prefs.data['payslip_footer'])]
    SimpleDocTemplate(buf,pagesize=A4,title='Payslip '+run.key).build(story)
    return buf.getvalue()

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
    from .reference_invoice import reference_invoice
    return reference_invoice(invoice, branding)


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

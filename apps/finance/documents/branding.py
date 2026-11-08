"""Request-local PDF branding; never mutate global ReportLab colours."""
from contextvars import ContextVar
from functools import wraps
from io import BytesIO
import base64
from reportlab.lib import colors
from reportlab.platypus import Image, Spacer, Table, TableStyle

_theme=ContextVar('document_theme',default={})
def themed_document(fn):
    @wraps(fn)
    def wrapped(*args,**kwargs):
        from apps.business.billing import settings
        document=next(iter(kwargs.values()),None)
        theme=settings(document.organization) if document and document.organization else {}
        token=_theme.set(theme)
        try:return fn(*args,**kwargs)
        finally:_theme.reset(token)
    return wrapped

def themed_color(value):
    original=colors.HexColor(value)
    accent=_theme.get().get('accent_color')
    if not accent:return original
    c=colors.HexColor(accent)
    # Tint light header/summary surfaces, leaving body text and borders legible.
    if value.upper() in ('#F2F2F2','#F4F4F4','#E8E8E8','#F3F4F6','#F8FAFC'):
        return colors.Color(.9+.1*c.red,.9+.1*c.green,.9+.1*c.blue)
    return original

def logo_story(theme=None):
    theme=_theme.get() if theme is None else theme
    value=theme.get('logo','')
    style=theme.get('document_style','classic')
    accent=colors.HexColor(theme.get('accent_color') or '#006b58')
    divider=Table([['']],colWidths=[500],rowHeights=[4 if style=='letterhead' else 1])
    divider.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),accent)]))
    extra=[divider,Spacer(1,10)] if style in ('letterhead','minimal') else []
    if not value:return extra
    try:
        prefix,data=value.split(',',1)
        if prefix not in ('data:image/png;base64','data:image/jpeg;base64'):return []
        img=Image(BytesIO(base64.b64decode(data,validate=True)))
        scale=min(100/img.imageWidth,45/img.imageHeight)
        img.drawWidth=img.imageWidth*scale;img.drawHeight=img.imageHeight*scale;img.hAlign='LEFT'
        return [img,Spacer(1,10)]+extra
    except (ValueError,OSError):return []

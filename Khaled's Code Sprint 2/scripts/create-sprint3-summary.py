from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
root=Path(__file__).resolve().parents[1];out=root/'output/pdf/FairGrade-Sprint3-Evaluation-Summary.pdf';out.parent.mkdir(parents=True,exist_ok=True)
fonts=Path('/usr/share/fonts/truetype/dejavu');pdfmetrics.registerFont(TTFont('FG',str(fonts/'DejaVuSans.ttf')));pdfmetrics.registerFont(TTFont('FG-Bold',str(fonts/'DejaVuSans-Bold.ttf')));pdfmetrics.registerFontFamily('FG',normal='FG',bold='FG-Bold',italic='FG',boldItalic='FG-Bold')
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='FGTitle',fontName='FG-Bold',fontSize=21,leading=25,spaceAfter=12,textColor=colors.HexColor('#154b3b')));styles.add(ParagraphStyle(name='FGBody',fontName='FG',fontSize=9,leading=13,spaceAfter=8));styles.add(ParagraphStyle(name='FGCell',fontName='FG',fontSize=8,leading=11))
p=lambda t:Paragraph(t,styles['FGBody']);c=lambda t:Paragraph(t,styles['FGCell'])
flow=[Paragraph('FairGrade / Sprint 3 evaluation',styles['FGTitle']),p('<b>Khaled - browser proctoring | Prepared 31 October 2026</b><br/>Omar\'s deployed API contract adopted. Earlier Lambda/SQL/Terraform proposal superseded.'),p('This table distinguishes executed software checks from field measurements that need the real laptop, authenticated HTTPS app and consenting participants. No simulated result is counted as human accuracy or AWS acceptance.')]
rows=[['Measure / requirement','Observed result','Scope / evidence'],
['Client and local demo tests','22 passed','Multipart POST, retries, errors, UUID/auth and local pipeline'],
['Statistics tests','5 passed','Flags/hour, confidence intervals, held-out identity analysis'],
['Legacy proposal regression','8 passed','Superseded local backend only; not Omar\'s API'],
['Browser integration checks','27 passed (9 + 5 + 13)','Local flow, mocked auth, embedding/review/flush; phase3 reports'],
['Nested model assets','All 3 systems ran; 25 asset requests','Actual blank-image inference; no isolation or SharedArrayBuffer'],
['Real-camera AWS pipeline','Not measured here','Missing test-account access, HTTPS session and physical webcam'],
['20-minute target-laptop session','Not measured; laptop model unknown','CPU %, process memory, FPS and trigger-to-log latency required'],
['Normal sessions / false flags','Not measured; rate and CI unknown','Required: five 10-minute sessions; at least 3 people with written consent'],
['Phone / second face / leaving','Not measured; misses and CI unknown','Required: 10 deliberate cases for each reason'],
['Identity swap','Not measured; misses and CI unknown','Required: 5 deliberate cases; self-captured reference'],
['Threshold changes','None','Existing defaults retained; no participant data supports tuning']]
table=Table([[c(v)for v in row]for row in rows],colWidths=[153,148,208]);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#deeee6')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#b9cfc4')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));flow.extend([table,Spacer(1,14),p('<b>Human analysis method:</b> false flags per armed monitoring hour with exact 95% Poisson intervals; deliberate detection rate and miss count with 95% Wilson intervals. No exposure means an unknown rate, not zero errors. Keep deliberate cases separate from normal exposure.'),p('<b>Limits:</b> self-captured reference, no liveness; visible tab required; page close can lose clips; YOLOv8n is AGPL-3.0 licensed; flags support human review and do not prove misconduct. See docs/LIMITATIONS.md.'),p('<b>Completion evidence needed:</b> follow docs/LIVE-ACCEPTANCE.md and TRIAL-PROTOCOL.md. Replace unknown field measurements only with operator-recorded results. AI assistance was used for this adaptation; Khaled must review and explain it.')])
def footer(canvas,doc):canvas.setFont('FG',8);canvas.setFillColor(colors.HexColor('#587267'));canvas.drawString(43,24,'FairGrade | Evidence status, not a claim of completed human trials');canvas.drawRightString(552,24,str(doc.page))
SimpleDocTemplate(str(out),pagesize=A4,leftMargin=43,rightMargin=43,topMargin=36,bottomMargin=38,title='FairGrade Sprint 3 Evaluation Summary',author='FairGrade project handoff').build(flow,onFirstPage=footer,onLaterPages=footer)
print(out)

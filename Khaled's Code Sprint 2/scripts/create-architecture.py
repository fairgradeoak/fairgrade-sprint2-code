from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
root=Path(__file__).resolve().parents[1];fig,ax=plt.subplots(figsize=(14,10));fig.patch.set_facecolor('#f4f8f5');ax.set_facecolor('#f4f8f5');ax.set_xlim(0,14);ax.set_ylim(0,10);ax.axis('off')
ax.text(.4,9.55,'FairGrade / Browser proctoring architecture',fontsize=23,weight='bold',color='#153b32')
ax.text(.4,9.12,'Sprint 3 - Omar\'s existing backend | 31 October 2026',fontsize=12,color='#547167')
def box(x,y,w,h,title,body,fill='#ffffff'):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=0.12',facecolor=fill,edgecolor='#b9cfc4',linewidth=1.4));ax.text(x+.2,y+h-.38,title,fontsize=14,weight='bold',color='#125c48');ax.text(x+.2,y+h-.73,body,fontsize=11,va='top',linespacing=1.55,color='#243e35')
def arrow(points,label=None,at=None):
 for a,b in zip(points[:-2],points[1:-1]):ax.plot([a[0],b[0]],[a[1],b[1]],color='#54776a',lw=1.6)
 ax.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',mutation_scale=14,color='#54776a',lw=1.6))
 if label:ax.text(*at,label,fontsize=10,color='#254b3e',ha='center',va='center',bbox=dict(facecolor='#f4f8f5',edgecolor='none',pad=2.5))
box(.4,7.3,5.3,1.35,'Host app + embeddable module','examId, token provider, container\nConsent, preview, status and instructor review')
box(8.1,7.3,5.3,1.35,'S3 + CloudFront assets','Relative JS / worker / WASM / model URLs\nHTTPS; no COOP/COEP or SharedArrayBuffer')
box(.4,4.95,5.3,1.45,'On-device detection','Camera: video only; RAM face reference\nMediaPipe + YOLOv8n + face-api.js')
box(8.1,4.95,5.3,1.45,'Omar API + Cognito','GET /policy; POST /clips/presign, /events\nInstructor list, playback and versioned review')
box(.4,2.65,5.3,1.45,'Trigger + evidence capture','Sustained signals; bounded rolling buffer\n7.5s before / after; MediaRecorder WebM')
box(8.1,2.65,5.3,1.45,'Private clips bucket','Multipart POST: signed fields, file last\n5-minute playback URL; 7-day clip retention')
box(8.1,.45,5.3,1.35,'Existing RDS event records','Event metadata and instructor decisions\nRemain with the exam record after clip deletion')
arrow([(8.1,7.95),(5.7,7.95)],'load assets',(6.9,8.18))
arrow([(3.05,7.3),(3.05,6.4)],'consent before camera',(3.05,6.87))
arrow([(3.05,4.95),(3.05,4.1)],'detections + captured frames',(3.05,4.53))
arrow([(5.7,7.3),(8.1,6.1)],'Bearer API calls',(6.85,6.87))
arrow([(5.7,4.0),(8.1,5.1)],'ticket / event',(6.85,4.62))
arrow([(5.7,3.18),(8.1,3.18)],'POST form\nno bearer token',(6.9,3.18))
arrow([(13.4,5.7),(13.8,5.7),(13.8,1.15),(13.4,1.15)])
ax.text(13.65,4.45,'save / review',fontsize=9,rotation=90,color='#54776a')
ax.text(.5,1.7,'Evidence supports human judgment.',fontsize=14,weight='bold',color='#153b32')
ax.text(.5,1.28,'No liveness check. No automatic misconduct decision.',fontsize=10.5,color='#547167')
ax.text(.5,.92,'stopProctoring stops camera, then drains captured clips.',fontsize=10.5,color='#547167')
ax.text(.5,.56,'Await completion before navigation; page close can lose clips.',fontsize=10.5,color='#547167')
fig.savefig(root/'docs/design/proctoring-architecture.png',dpi=180,bbox_inches='tight',facecolor=fig.get_facecolor());plt.close(fig)

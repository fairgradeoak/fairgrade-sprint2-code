"""Convert stopped browser exports to a candidate dataset. Review before summarizing."""
import argparse,json,uuid
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('files',nargs='+');p.add_argument('--output',required=True);a=p.parse_args()
result={'sessions':[],'identityTrials':[],'detectionCases':[]}
for filename in a.files:
 data=json.loads(Path(filename).read_text());t=data.get('telemetry') or {};meta=data.get('trial') or {}
 if t.get('synthetic') is not False or not t.get('ended') or not meta.get('participantConsent') or t.get('truncated'):raise ValueError(f'{filename}: only stopped, consenting, non-synthetic, untruncated sessions can be imported')
 # Stable export identity prevents accidental duplicate import of the same run.
 sid=str(uuid.uuid5(uuid.NAMESPACE_URL,'fairgrade:'+t['startedAt']+':'+meta.get('alias','')))
 result['sessions'].append({'sessionId':sid,'source':Path(filename).name,'alias':meta.get('alias'),'round':meta.get('round'),'scenario':meta.get('scenario'),'synthetic':False,'participantConsent':True,'reviewed':False,'armedSeconds':t['armedMs']/1000,'thresholds':t['thresholds'],'flags':[dict(f,falsePositive=None) for f in t.get('flags',[])]})
 result['identityTrials'].extend(t.get('identityTrials',[]))
Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
print('Candidate dataset saved. Adjudicate every flag and mark each completed session reviewed; keep deliberate scenarios out of normal-behavior exposure.')

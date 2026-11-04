"""Human evaluation only. Exact Poisson flag-rate CI; Wilson detection-rate CI.
No invented observations and no automatic edits to production thresholds.
"""
import argparse
import json
import math
from pathlib import Path
from scipy.stats import chi2

ROUNDS=('baseline','tuned','integrated')
REASONS=('phone','second_face','identity_mismatch','no_face')
def number(value,minimum=0):
 return type(value) in (int,float) and math.isfinite(value) and value>=minimum

def poisson(count,hours):
 if not hours:return {'count':count,'hours':0,'perHour':None,'ci95':None}
 low=0 if count==0 else chi2.ppf(.025,2*count)/2/hours
 high=chi2.ppf(.975,2*(count+1))/2/hours
 return {'count':count,'hours':hours,'perHour':count/hours,'ci95':[float(low),float(high)]}

def wilson(success,total):
 if not total:return {'success':0,'total':0,'rate':None,'ci95':None}
 z=1.959963984540054;p=success/total;d=1+z*z/total
 center=(p+z*z/(2*total))/d;half=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/d
 return {'success':success,'total':total,'rate':p,'ci95':[max(0,center-half),min(1,center+half)]}

def identity_summary(trials):
 ids=set()
 for t in trials:
  if not t.get('trialId') or t['trialId'] in ids:raise ValueError('Missing/duplicate identity trial ID')
  ids.add(t['trialId'])
  if not number(t.get('distance')) or not 0<=t['distance']<=2 or t.get('split') not in {'calibration','validation'} or type(t.get('genuine')) is not bool or t.get('participantConsent') is not True or not t.get('alias') or not t.get('referenceAlias') or t['genuine']!=(t['alias']==t['referenceAlias']):raise ValueError('Invalid identity trial')
 aliases={t['alias'] for t in trials}|{t['referenceAlias'] for t in trials}
 calibration=[t for t in trials if t['split']=='calibration'];validation=[t for t in trials if t['split']=='validation']
 def metrics(items,threshold):
  genuine=[t for t in items if t['genuine']];impostor=[t for t in items if not t['genuine']]
  return {'falseAccept':wilson(sum(t['distance']<=threshold for t in impostor),len(impostor)), 'falseReject':wilson(sum(t['distance']>threshold for t in genuine),len(genuine))}
 if len(aliases)<3 or not any(t['genuine'] for t in calibration) or not any(not t['genuine'] for t in calibration):return {'status':'insufficient_data','aliases':len(aliases),'recommendedThreshold':None}
 values=sorted({t['distance'] for t in calibration});candidates=sorted({0,2,*values,*[(a+b)/2 for a,b in zip(values,values[1:])]})
 scores=[]
 for threshold in candidates:
  m=metrics(calibration,threshold);far=m['falseAccept']['rate'];frr=m['falseReject']['rate']
  if far<=.05:scores.append(((far+frr)/2,threshold))
 if not scores:return {'status':'no_threshold_meets_calibration_false_accept_cap','recommendedThreshold':None}
 threshold=min(scores)[1]
 return {'status':'candidate_only_requires_held_out_validation','aliases':len(aliases),'recommendedThreshold':threshold,'selection':'Lowest balanced error among calibration FAR <= 5%; lower threshold breaks ties','calibration':metrics(calibration,threshold),'validation':metrics(validation,threshold),'limitations':['No liveness','Self-captured reference does not establish institutional identity','Repeated frames and attempts are correlated','Small samples cannot establish a reliable false-accept bound']}

def summarize(data):
 sessions=data.get('sessions',[]);cases=data.get('detectionCases',[]);ids=set();out={}
 for s in sessions:
  if s.get('synthetic') is not False or s.get('participantConsent') is not True or s.get('reviewed') is not True or s.get('round') not in ROUNDS or not number(s.get('armedSeconds'),.001) or not s.get('alias'):raise ValueError('Only completed, reviewed, consenting human sessions with armed exposure are accepted')
  if not s.get('sessionId') or s['sessionId'] in ids:raise ValueError('Missing/duplicate session ID')
  ids.add(s['sessionId']);flags=s.get('flags',[])
  if len({f.get('eventId') for f in flags})!=len(flags):raise ValueError('Duplicate flag event IDs')
  for f in flags:
   if not f.get('eventId') or f.get('reason') not in REASONS or type(f.get('falsePositive')) is not bool:raise ValueError('Every flag needs a reviewed falsePositive boolean and reason')
 for c in cases:
  if c.get('synthetic') is not False or c.get('participantConsent') is not True or c.get('round') not in ROUNDS or c.get('reason') not in REASONS or type(c.get('detected')) is not bool or not c.get('caseId') or c['caseId'] in ids:raise ValueError('Invalid/duplicate deliberate detection case')
  ids.add(c['caseId'])
 for rnd in ROUNDS:
  rows=[s for s in sessions if s['round']==rnd];hours=sum(s['armedSeconds'] for s in rows)/3600;flags=[f for s in rows for f in s.get('flags',[])]
  out[rnd]={'configurations':[json.loads(c) for c in sorted({json.dumps(row.get('thresholds',{}),sort_keys=True) for row in rows})],'participants':len({s['alias'] for s in rows}),'sessions':len(rows),'allFlags':poisson(len(flags),hours),'falseFlags':poisson(sum(f['falsePositive'] for f in flags),hours),
    'falseFlagsByReason':{reason:poisson(sum(f['falsePositive'] and f['reason']==reason for f in flags),hours) for reason in REASONS},
    'detection':{reason:wilson(sum(c['detected'] for c in cases if c['round']==rnd and c['reason']==reason),sum(c['round']==rnd and c['reason']==reason for c in cases)) for reason in REASONS}}
 return {'status':'measured_human_data' if sessions or cases else 'not_run','rounds':out,'identity':identity_summary(data.get('identityTrials',[])),
  'interpretation':['Flags/hour uses armed monitoring exposure only, excluding enrollment and warmup','Poisson confidence intervals assume independent events at constant rate; clustering by participant can make intervals optimistic','Wilson intervals use deliberate attempts, not frames; report unknown/aborted attempts separately','Changing cooldowns affects flags/hour: compare configurations and detection rates together','Zero observations is not zero error; no-data rates remain null']}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('input');parser.add_argument('--output');args=parser.parse_args()
 result=summarize(json.loads(Path(args.input).read_text()));text=json.dumps(result,indent=2,allow_nan=False)+'\n'
 if args.output:Path(args.output).write_text(text)
 else:print(text)
if __name__=='__main__':main()

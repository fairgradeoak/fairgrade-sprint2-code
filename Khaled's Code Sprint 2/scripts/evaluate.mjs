// Compatibility entry point for the phase-2 summary utility (Python + SciPy required).
import{spawnSync}from'node:child_process';
const input=process.argv[2]||'evaluation/trials.json',output=process.argv[3]||'evaluation/phase3-summary.json';
const result=spawnSync(process.env.PYTHON||'python',['scripts/summarize.py',input,'--output',output],{stdio:'inherit'});
if(result.error)console.error(result.error.message);process.exitCode=result.status??1;

"""Package the complete repository as three independently readable ZIPs.
Extract all three into the same parent directory. No dependencies/private data.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import zipfile

def main():
 parser=argparse.ArgumentParser();parser.add_argument('output_dir');args=parser.parse_args()
 root=Path(__file__).resolve().parents[3];out=Path(args.output_dir).resolve();out.mkdir(parents=True,exist_ok=True)
 public=Path('Khaled_Code/FairGrade-Proctoring/public')
 groups={'Code':[],'Vendor':[],'Models':[]}
 skip={'.git','node_modules','__pycache__','.pytest_cache','.venv','data','private','test-results','var','fontcache','.terraform','dist'}
 for directory,dirs,files in os.walk(root):
  dirs[:]=[d for d in dirs if d not in skip]
  for filename in sorted(files):
   p=Path(directory)/filename;rel=p.relative_to(root)
   if p.is_symlink() or filename.endswith(('.pyc','.zip','.tfstate','.tfvars')) or '.tfstate.' in filename:continue
   if filename.startswith('.env') and filename!='.env.example':continue
   if rel.as_posix()=='DELIVERY-ASSETS.json':continue
   group='Vendor' if rel.is_relative_to(public/'vendor') else 'Models' if rel.is_relative_to(public/'models') else 'Code'
   groups[group].append(rel)
 results=[]
 for group in ['Vendor','Models','Code']:
  if group=='Code':
   manifest=root/'DELIVERY-ASSETS.json'
   manifest.write_text(json.dumps({'extraction':'Extract all three archives into the SAME parent folder. They share the FairGrade root.','assetArchives':results,'assetVerification':'Run node scripts/verify-models.mjs inside FairGrade/Khaled_Code/FairGrade-Proctoring after extracting.'},indent=2)+'\n')
   groups[group].append(manifest.relative_to(root))
  target=out/f'FairGrade-Nov03-{group}.zip'
  with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
   for rel in sorted(groups[group]):z.write(root/rel,(Path('FairGrade')/rel).as_posix())
  with zipfile.ZipFile(target) as z:
   assert z.testzip() is None
   for rel in groups[group]:assert z.read((Path('FairGrade')/rel).as_posix())==(root/rel).read_bytes(),str(rel)
  assert target.stat().st_size<25*1024*1024,'Archive too large for this delivery; split again'
  results.append({'file':target.name,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'files':len(groups[group]),'integrity':'CRC and every uncompressed byte compared with source'})
 print(json.dumps(results,indent=2))

if __name__=='__main__':main()

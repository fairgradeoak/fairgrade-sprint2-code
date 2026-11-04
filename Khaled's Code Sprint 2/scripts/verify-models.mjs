import{readFile}from'node:fs/promises';import{createHash}from'node:crypto';import{resolve,sep}from'node:path';
const root=resolve('public'),manifest=JSON.parse(await readFile(resolve(root,'models/provenance.json')));
for(const entry of manifest.files){const path=resolve(root,entry.file);if(!path.startsWith(root+sep))throw Error('Unsafe provenance path');const data=await readFile(path);if(data.length!==entry.bytes||createHash('sha256').update(data).digest('hex')!==entry.sha256)throw Error(`Asset mismatch: ${entry.file}`);}
console.log(`Verified ${manifest.files.length} installed model/vendor assets by SHA-256.`);

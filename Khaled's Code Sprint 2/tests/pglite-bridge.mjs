// PostgreSQL WASM engine for isolated handler/SQL tests; NOT a substitute for RDS tests.
import {PGlite} from '@electric-sql/pglite';import {createInterface} from 'node:readline';
const db=new PGlite();await db.waitReady;
for await(const line of createInterface({input:process.stdin})){
 try{const {sql,params=[],exec=false}=JSON.parse(line);const result=exec?await db.exec(sql):await db.query(sql,params);process.stdout.write(JSON.stringify({ok:true,result})+'\n');}
 catch(e){process.stdout.write(JSON.stringify({ok:false,error:e.message,code:e.code})+'\n');}
}
await db.close();

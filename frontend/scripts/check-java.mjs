import {spawnSync} from 'node:child_process';
import path from 'node:path';
const java=process.env.JAVA_HOME?path.join(process.env.JAVA_HOME,'bin','java.exe'):'java';
const r=spawnSync(java,['-version'],{encoding:'utf8'});
const output=(r.stderr||'')+(r.stdout||'');
const major=Number(output.match(/version "(\d+)/)?.[1]);
if(r.error||r.status!==0||major!==21){console.error('This Android project requires JDK 21. Set JAVA_HOME to an installed JDK 21 folder, then retry. Java 25 causes Unsupported class file major version 69. Detected:',major||'not available');process.exit(1);}
console.log('Java 21 verified.');

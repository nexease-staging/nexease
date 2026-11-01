import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
process.env.NEXEASE_MOBILE = 'true';
if(existsSync('android/app/google-services.json')) process.env.NEXT_PUBLIC_PUSH_ENABLED='true';
process.env.NEXT_PUBLIC_MOBILE_APP = 'true';
process.env.NEXT_TELEMETRY_DISABLED = '1';
const result = spawnSync(process.execPath, ['node_modules/next/dist/bin/next', 'build', '--webpack'], { stdio:'inherit', env:process.env });
process.exit(result.status ?? 1);

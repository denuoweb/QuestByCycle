const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'));
let commit = 'dev';
try {
  commit = execSync('git rev-parse --short HEAD').toString().trim();
} catch {}

const version = `${pkg.version}-${commit}`;
const swPath = path.join(__dirname, '..', 'frontend', 'sw.js');
let content = fs.readFileSync(swPath, 'utf8');
content = content.replace(/const VERSION = '.*?';/, `const VERSION = '${version}';`);
fs.writeFileSync(swPath, content);
console.log('Service worker version set to', version);

const path = require('path');
const fs = require('fs');

const extDir = path.resolve('extension');
process.chdir(extDir);

const ts = require(path.join(extDir, 'node_modules/typescript'));
console.log('Using TypeScript version:', ts.version);

const configPath = path.join(extDir, 'tsconfig.json');
const configFile = ts.readConfigFile(configPath, ts.sys.readFile);

if (configFile.error) {
  console.error('Error reading tsconfig.json:', configFile.error);
  process.exit(1);
}

const parsed = ts.parseJsonConfigFileContent(configFile.config, ts.sys, extDir);
console.log('Files to compile count:', parsed.fileNames.length);

const program = ts.createProgram(parsed.fileNames, {
  ...parsed.options,
  noEmit: true
});

const diagnostics = ts.getPreEmitDiagnostics(program);

if (diagnostics.length > 0) {
  console.error(`Found ${diagnostics.length} diagnostic error(s):`);
  for (const diag of diagnostics) {
    const file = diag.file ? path.relative(extDir, diag.file.fileName) : 'global';
    const msg = typeof diag.messageText === 'string' ? diag.messageText : diag.messageText.messageText;
    const line = diag.file && diag.start !== undefined ? diag.file.getLineAndCharacterOfPosition(diag.start).line + 1 : 0;
    console.error(`  ${file}:${line} - ${msg}`);
  }
  process.exit(1);
} else {
  console.log('✅ TypeScript type check passed with 0 errors!');
  process.exit(0);
}

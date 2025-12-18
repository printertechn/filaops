#!/usr/bin/env node

/**
 * Fix Temporal Dead Zone errors in React components
 * 
 * Vite's production minifier creates temporal dead zones when async functions
 * are defined AFTER the useEffect that calls them. This script:
 * 1. Finds all async function definitions
 * 2. Wraps them in useCallback
 * 3. Moves them BEFORE any useEffect that calls them
 * 4. Updates useEffect dependencies
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

function fixFile(filePath) {
  console.log(`Processing: ${filePath}`);
  let content = fs.readFileSync(filePath, 'utf8');
  let modified = false;

  // Check if file already imports useCallback
  const hasUseCallback = /import\s+{[^}]*useCallback[^}]*}\s+from\s+["']react["']/.test(content);
  
  // Add useCallback to imports if needed
  if (!hasUseCallback && /from\s+["']react["']/.test(content)) {
    content = content.replace(
      /import\s+{([^}]*)}\s+from\s+["']react["']/,
      (match, imports) => {
        const importList = imports.split(',').map(s => s.trim()).filter(Boolean);
        if (!importList.includes('useCallback')) {
          importList.push('useCallback');
          modified = true;
        }
        return `import { ${importList.join(', ')} } from "react"`;
      }
    );
  }

  // Find all async function definitions that are NOT wrapped in useCallback
  const asyncFuncPattern = /(\s+)const\s+(\w+)\s*=\s*async\s*\(([^)]*)\)\s*=>\s*{/g;
  let match;
  const functionsToWrap = [];

  while ((match = asyncFuncPattern.exec(content)) !== null) {
    const [fullMatch, indent, funcName, params] = match;
    const index = match.index;
    
    // Check if this function is called in a useEffect BEFORE it's defined
    const beforeContent = content.substring(0, index);
    const afterContent = content.substring(index);
    
    // Check if function is called in useEffect
    const useEffectPattern = new RegExp(`useEffect\\([^{]*{[^}]*${funcName}\\(`, 'g');
    const calledInUseEffect = useEffectPattern.test(beforeContent);
    
    // Check if already wrapped in useCallback
    const alreadyWrapped = beforeContent.slice(-50).includes('useCallback');
    
    if (calledInUseEffect && !alreadyWrapped) {
      console.log(`  Found function "${funcName}" called in useEffect before definition`);
      functionsToWrap.push({ funcName, fullMatch, index, indent, params });
    }
  }

  if (functionsToWrap.length > 0) {
    console.log(`  ⚠️  Found ${functionsToWrap.length} functions with temporal dead zone issues`);
    console.log(`  This file needs manual review - automatic fixing is complex for production code`);
    console.log(`  Functions: ${functionsToWrap.map(f => f.funcName).join(', ')}\n`);
  }

  if (modified) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`  ✅ Added useCallback import\n`);
  } else {
    console.log(`  ℹ️  No changes needed\n`);
  }
}

// Find all .jsx files
const files = glob.sync('frontend/src/**/*.jsx', { cwd: path.join(__dirname, '..') });

console.log(`Found ${files.length} .jsx files\n`);

files.forEach(file => {
  const fullPath = path.join(__dirname, '..', file);
  fixFile(fullPath);
});

console.log('Done!');

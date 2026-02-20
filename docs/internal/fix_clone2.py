#!/usr/bin/env python3
"""Fix clone port (8095→8092) + patch hFile in editor.html"""
import os

# 1. Fix port in clone_server.py
f1 = '/opt/windi/clone-app/clone_server.py'
c = open(f1).read()
c = c.replace('"port": 8095', '"port": 8092')
c = c.replace('port=8095', 'port=8092')
c = c.replace('0.0.0.0:8095', '0.0.0.0:8092')
open(f1, 'w').write(c)
print('✅ Port fixed: 8095 → 8092')

# 2. Patch hFile in editor.html
f2 = '/opt/windi/clone-app/static/editor.html'
c = open(f2).read()

old = 'async function hFile(f){'
if old not in c:
    print('❌ hFile not found'); exit(1)

start = c.index(old)
bc = 0; end = start; ff = False
for i in range(start, min(start+600, len(c))):
    if c[i] == '{': bc += 1; ff = True
    elif c[i] == '}':
        bc -= 1
        if ff and bc == 0: end = i + 1; break

new = """async function hFile(f){
  if(!f)return;
  const dt=document.getElementById('dt');
  const tw=document.getElementById('tw');
  tw.classList.add('op');
  if(f.name.endsWith('.txt')||f.name.endsWith('.md')){
    dt.value=await f.text();scan();
  } else if(f.name.endsWith('.pdf')||f.name.endsWith('.docx')||f.name.endsWith('.doc')){
    dt.value='\\u23f3 Dokument wird analysiert...';dt.disabled=true;
    try{
      const fd=new FormData();fd.append('file',f);
      const res=await fetch('/api/extract',{method:'POST',body:fd});
      const data=await res.json();
      if(data.success&&data.text){dt.value=data.text;dt.disabled=false;scan();}
      else{dt.value='';dt.disabled=false;dt.placeholder=data.error||'Extraktion fehlgeschlagen';dt.focus();}
    }catch(e){dt.value='';dt.disabled=false;dt.placeholder='Server nicht erreichbar';dt.focus();}
  } else { dt.focus(); }
}"""

c = c[:start] + new + c[end:]
open(f2, 'w').write(c)
print('✅ hFile patched in editor.html')

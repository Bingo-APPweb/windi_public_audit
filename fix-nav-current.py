#!/usr/bin/env python3
"""
Fix: Add nav-current styling to all Library pages
- CSS: .nav-links a.nav-current { ... }
- JS: Mark Library link as current when on /library/ pages
"""

import os
import glob

DIR = "/opt/windi/masterarbeit"

CSS_RULE = '.nav-links a.nav-current { color: var(--dim); pointer-events: none; opacity: 0.5; }'

JS_CODE = '''
// Mark current nav link
if(location.pathname.includes('/library/')){
  document.querySelectorAll('.nav-links a').forEach(function(a){
    if(a.getAttribute('href')==='/library/' || a.getAttribute('href')==='/library/index.html'){
      a.classList.add('nav-current');
    }
  });
}
'''

css_added = 0
js_added = 0

for filepath in glob.glob(f"{DIR}/*.html"):
    filename = os.path.basename(filepath)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    modified = False

    # Add CSS if not present
    if 'nav-current' not in content:
        # Find the nav-links a:hover line and add after it
        old = '.nav-links a:hover { color: var(--gold); }'
        if old in content:
            new = old + '\n' + CSS_RULE
            content = content.replace(old, new)
            css_added += 1
            modified = True

    # Add JS if not present
    if "Mark current nav link" not in content:
        # Add before </script>
        if '</script>' in content:
            content = content.replace('</script>', JS_CODE + '</script>', 1)
            js_added += 1
            modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ {filename}")

print()
print(f"CSS added to: {css_added} files")
print(f"JS added to: {js_added} files")

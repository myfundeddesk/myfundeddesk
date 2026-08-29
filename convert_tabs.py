import re

for tab in ['tab_packages.html', 'tab_trades.html', 'tab_settings.html']:
    with open(tab, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 1. Update the outer div
    html = re.sub(r'<div id="(tab-[a-z]+)" class="tab-content">', r'<div id="\1" class="admin-tab" style="display: none;">\n    <div class="row">\n        <div class="col-xl-12">\n            <div class="card b-radius--10 mb-4">', html)
    
    # 2. Update window-header to card-header
    html = re.sub(r'<div class="window-header">\n\s*<h2[^>]*><i[^>]*></i>\s*(.*?)\s*</h2>\n\s*</div>', r'<div class="card-header d-flex justify-content-between align-items-center">\n                <h5>\1</h5>\n            </div>\n            <div class="card-body p-4">', html)
    
    # 3. Add closing tags for card-body, card, col, row
    # In the original, the tab-content closes with </div>.
    # We replaced the opening with 4 nested divs, so we need 4 closing divs.
    # Actually, we can just replace the final </div> with </div></div></div></div></div>
    
    # Let's just do a naive conversion for now. I'll just change the class names.
    # Resetting the script to do it simpler:
    
    with open(tab, 'r', encoding='utf-8') as f:
        html = f.read()
        
    html = html.replace('class="tab-content"', 'class="admin-tab" style="display: none;"')
    
    # Replace the inner window classes with ViserLab card classes so they look good
    html = html.replace('class="window-header"', 'class="card-header d-flex justify-content-between align-items-center"')
    html = html.replace('class="window-body"', 'class="card-body"')
    
    # Convert old tables to ViserLab tables
    html = html.replace('class="w-full text-left border-collapse text-sm text-slate-300"', 'class="table table--light style--two"')
    html = html.replace('class="bg-darkborder/50 text-slate-400 uppercase text-[10px] tracking-wider"', 'class="bg--dark"')
    
    # Convert old inputs
    html = html.replace('class="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white"', 'class="form-control"')
    
    # Convert old buttons
    html = html.replace('class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded shadow transition-colors text-sm"', 'class="btn btn-primary"')
    html = html.replace('class="px-3 py-1 bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 rounded text-xs"', 'class="btn btn-sm btn-outline--primary"')
    html = html.replace('class="px-3 py-1 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded text-xs"', 'class="btn btn-sm btn-outline--danger"')
    
    with open(tab, 'w', encoding='utf-8') as f:
        f.write(html)
        
print("Converted tabs to new layout classes.")

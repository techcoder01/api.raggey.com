import re

# Read urls.py
with open('raggyBackend/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if favicon route already exists
if "path('favicon.ico'" not in content:
    # Add favicon route after path('', home),
    content = content.replace(
        "path('', home),",
        "path('', home),\n    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),"
    )
    
    # Write back
    with open('raggyBackend/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Favicon route added successfully!")
else:
    print("ℹ️  Favicon route already exists")

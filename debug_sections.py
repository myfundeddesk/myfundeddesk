with open("app/templates/landing.html", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = re.finditer(r'<section', text)
print("Number of sections:", len(list(matches)))

# Count pricing sections
print("Number of pricingData():", text.count("pricingData()"))

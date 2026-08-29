with open("app/templates/landing.html", "r", encoding="utf-8") as f:
    text = f.read()

# Replace hardcoded hero text with dynamic Jinja variables
text = text.replace("Built for <span class=\"text-white\">Traders.</span>", "{{ landing_data.hero_title_1.replace('Traders.', '<span class=\"text-white\">Traders.</span>') | safe }}")
text = text.replace("Funded by Us.", "{{ landing_data.hero_title_2 }}")
text = text.replace("We provide up to <strong class=\"text-white\">?1,00,00,000</strong> in real capital. You keep <strong class=\"text-emerald-400\">90% of the profits</strong>. No hidden rules. No excuses. Just pure trading.", "{{ landing_data.hero_subtitle }}")
text = text.replace("?? Update 2.0: 100k Instant account", "{{ landing_data.announcement_text }}")

with open("app/templates/landing.html", "w", encoding="utf-8") as f:
    f.write(text)
print("Landing page mapped to Customizer variables!")

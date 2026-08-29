with open('app/templates/landing.html', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('<style>')
end = text.find('</style>') + 8

bg_html = """
    <style>
        body {
            background-color: #02040a;
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(16, 185, 129, 0.08), transparent 25%),
                radial-gradient(circle at 85% 30%, rgba(16, 185, 129, 0.12), transparent 25%),
                url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
            color: #f8fafc;
            font-family: 'Inter', sans-serif;
        }
        .text-gradient {
            background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .glass-card {
            background: rgba(13, 16, 23, 0.7);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(30, 35, 48, 0.8);
        }
    </style>
"""

new_text = text[:start] + bg_html + text[end:]

with open('app/templates/landing.html', 'w', encoding='utf-8') as f:
    f.write(new_text)

print('Updated landing.html with dark starry background!')

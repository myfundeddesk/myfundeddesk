with open('app/templates/landing.html', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('<!-- Top Announcement Bar -->')
end = text.find('<!-- Ticker Tape -->')

nav_html = """
    <!-- Top Announcement Bar -->
    <div class="bg-emerald-500 text-black text-center py-2 text-sm font-bold tracking-wide">
        ?? Update 2.0: 100k Instant account
    </div>

    <!-- Navigation -->
    <nav class="fixed w-full z-50 transition-all duration-300 bg-[#05070a]/80 backdrop-blur-md border-b border-[#1e2330]">
        <div class="max-w-7xl mx-auto px-6">
            <div class="flex justify-between items-center h-20">
                
                <!-- Logo -->
                <a href="/" class="flex items-center gap-2 group">
                    <div class="font-black text-2xl tracking-tighter text-white flex items-center gap-1">
                        <svg class="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M4 4h4v4H4zm6 0h4v4h-4zm6 0h4v4h-4zM4 10h4v4H4zm6 0h4v4h-4zm6 0h4v4h-4zM4 16h4v4H4zm6 0h4v4h-4zm6 0h4v4h-4z" />
                        </svg>
                        FUNDED <span class="font-medium text-slate-300">FIRM</span>
                    </div>
                </a>

                <!-- Desktop Menu -->
                <div class="hidden lg:flex items-center gap-6 bg-[#0d1017] border border-[#1e2330] rounded-full px-6 py-2.5 shadow-lg">
                    <a href="/" class="text-emerald-500 font-bold text-sm hover:text-emerald-400 transition-colors">
                        <span class="text-emerald-500/50 mr-1">0.1 /</span> Home
                    </a>
                    <a href="/rules" class="text-slate-300 font-bold text-sm hover:text-emerald-500 transition-colors">
                        <span class="text-emerald-500/50 mr-1">0.2 /</span> Trading Rules
                    </a>
                    <a href="#insights" class="text-slate-300 font-bold text-sm hover:text-emerald-500 transition-colors flex items-center gap-1">
                        <span class="text-emerald-500/50 mr-1">0.3 /</span> Insights <i data-lucide="chevron-down" class="w-3 h-3"></i>
                    </a>
                    <a href="#faq" class="text-slate-300 font-bold text-sm hover:text-emerald-500 transition-colors">
                        <span class="text-emerald-500/50 mr-1">0.4 /</span> FAQ
                    </a>
                    <a href="#contact" class="text-slate-300 font-bold text-sm hover:text-emerald-500 transition-colors">
                        <span class="text-emerald-500/50 mr-1">0.5 /</span> Contact Us
                    </a>
                </div>

                <div class="flex items-center gap-6">
                    {% if user %}
                        <a href="/dashboard" class="text-slate-300 hover:text-white text-sm font-bold transition-colors">Dashboard</a>
                    {% else %}
                        <a href="/login" class="text-slate-300 hover:text-white text-sm font-bold hidden md:block transition-colors">Login</a>
                        <a href="/register" class="bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 hover:bg-emerald-500 hover:text-black px-6 py-2.5 rounded-full text-sm font-black transition-all flex items-center gap-2">
                            Get Funded <i data-lucide="arrow-right" class="w-4 h-4"></i>
                        </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </nav>
"""

new_text = text[:start] + nav_html + text[end:]

with open('app/templates/landing.html', 'w', encoding='utf-8') as f:
    f.write(new_text)

print('Updated landing.html with FundedFirm navbar!')

with open('app/templates/landing.html', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('<!-- 5. PRICING -->')
end = text.find('</section>', start) + 10

pricing_html = """
    <!-- 5. PRICING -->
    <section id="pricing" class="py-32 relative z-20" x-data="pricingData()">
        <div class="max-w-3xl mx-auto px-6">
            <div class="text-center mb-16">
                <h2 data-aos="fade-up" class="text-4xl md:text-6xl font-black mb-8 text-white">Funded Account <span class="text-emerald-500">Challenges</span></h2>
                
                <!-- Model Toggle -->
                <div class="inline-flex p-1 bg-[#0d1017] border border-[#1e2330] rounded-full mb-6" data-aos="fade-up" data-aos-delay="100">
                    <template x-for="model in models" :key="model">
                        <button @click="activeModel = model" 
                                :class="activeModel === model ? 'bg-emerald-500 text-black shadow-lg shadow-emerald-500/20' : 'text-slate-400 hover:text-white'"
                                class="px-6 py-2.5 rounded-full text-sm font-bold tracking-wide transition-all uppercase" x-text="model">
                        </button>
                    </template>
                </div>

                <!-- Size Toggle -->
                <div class="flex flex-wrap justify-center gap-2" data-aos="fade-up" data-aos-delay="200">
                    <template x-for="size in uniqueSizes" :key="size">
                        <div class="relative">
                            <template x-if="size === 100000">
                                <div class="absolute -top-3 -right-2 bg-emerald-100 text-emerald-800 text-[9px] font-black px-2 py-0.5 rounded-full whitespace-nowrap z-10">Most Popular</div>
                            </template>
                            <button @click="activeSize = size" 
                                    :class="activeSize === size ? 'bg-emerald-500 text-black border-emerald-500' : 'bg-[#0d1017] text-slate-300 border-[#1e2330] hover:border-emerald-500/50'"
                                    class="px-6 py-2 rounded-full text-sm font-bold border transition-all" x-text="formatK(size)">
                            </button>
                        </div>
                    </template>
                </div>
            </div>

            <!-- Price Card -->
            <div class="bg-[#05070a] border border-[#1e2330] rounded-3xl p-8 md:p-12 shadow-2xl relative overflow-hidden" data-aos="fade-up" data-aos-delay="300">
                <div class="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl"></div>
                
                <template x-if="currentPkg">
                    <div>
                        <div class="text-emerald-500 font-bold mb-6" x-text="currentPkg.model_type"></div>
                        
                        <div class="flex items-end gap-4 mb-4">
                            <div class="text-2xl text-amber-500 font-bold line-through" x-text="'?' + Math.floor(currentPkg.price * 1.2).toLocaleString('en-IN')"></div>
                            <div class="text-5xl font-black text-white" x-text="'?' + Math.floor(currentPkg.price).toLocaleString('en-IN')"></div>
                            <div class="bg-amber-900/40 border border-amber-500/30 text-amber-500 text-[10px] font-bold px-2 py-1 rounded uppercase tracking-wider mb-2">Limited Time Offer</div>
                        </div>

                        <div class="flex gap-3 mb-8">
                            <div class="flex items-center gap-1 text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full">
                                <i data-lucide="refresh-ccw" class="w-3 h-3"></i> Swap Free
                            </div>
                            <div class="flex items-center gap-1 text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full">
                                <i data-lucide="dollar-sign" class="w-3 h-3"></i> Commission Free
                            </div>
                        </div>

                        <div class="text-slate-400 font-medium mb-8">Risk Reward Matters</div>

                        <a href="/buy-challenge" class="block w-full text-center bg-transparent border border-emerald-500 text-emerald-500 hover:bg-emerald-500 hover:text-black font-bold py-4 rounded-xl transition-all mb-8 uppercase tracking-widest text-sm">
                            Buy Plan
                        </a>

                        <div class="space-y-4 text-sm">
                            <div class="flex justify-between items-center py-3 border-b border-[#1e2330]">
                                <span class="text-slate-400 font-medium">Profit Target:</span>
                                <span class="text-white font-bold" x-text="currentPkg.profit_target_p1 + '%'"></span>
                            </div>
                            <div class="flex justify-between items-center py-3 border-b border-[#1e2330]">
                                <span class="text-slate-400 font-medium">Maximum Daily Loss:</span>
                                <span class="text-white font-bold" x-text="currentPkg.max_daily_loss + '%'"></span>
                            </div>
                            <div class="flex justify-between items-center py-3 border-b border-[#1e2330]">
                                <span class="text-slate-400 font-medium">Maximum Overall Loss:</span>
                                <span class="text-white font-bold" x-text="currentPkg.max_total_loss + '%'"></span>
                            </div>
                            <div class="flex justify-between items-center py-3 border-b border-[#1e2330]">
                                <span class="text-slate-400 font-medium">Minimum Trading Days:</span>
                                <span class="text-white font-bold" x-text="currentPkg.min_trading_days + ' Days'"></span>
                            </div>
                            <div class="flex justify-between items-center py-3 border-b border-[#1e2330]">
                                <span class="text-slate-400 font-medium">Profit Split Upto:</span>
                                <span class="text-white font-bold">100%</span>
                            </div>
                            <div class="flex justify-between items-center py-3 border-b border-[#1e2330]">
                                <span class="text-slate-400 font-medium">News Trading:</span>
                                <span class="text-emerald-500 font-bold">?</span>
                            </div>
                            <div class="flex justify-between items-center py-3 border-b border-[#1e2330]">
                                <span class="text-slate-400 font-medium">Reward Cycle:</span>
                                <span class="text-white font-bold">Monthly/Biweekly/Weekly</span>
                            </div>
                        </div>
                    </div>
                </template>
                <template x-if="!currentPkg">
                    <div class="text-center py-12 text-slate-500">
                        No package matches the selected configuration.
                    </div>
                </template>
            </div>
        </div>
    </section>
"""

new_text = text[:start] + pricing_html + text[end:]

script_html = """
<script>
    function pricingData() {
        return {
            models: ['1-Step', '2-Step', 'Instant'],
            activeModel: '2-Step',
            activeSize: 100000,
            packages: [
                {% for pkg in packages %}
                {
                    id: {{ pkg.id }},
                    name: "{{ pkg.name }}",
                    model_type: "{{ pkg.model_type }}",
                    account_size: {{ pkg.account_size }},
                    price: {{ pkg.price }},
                    profit_target_p1: {{ pkg.profit_target_p1 }},
                    profit_target_p2: {{ pkg.profit_target_p2 }},
                    max_daily_loss: {{ pkg.max_daily_loss }},
                    max_total_loss: {{ pkg.max_total_loss }},
                    min_trading_days: {{ pkg.min_trading_days }}
                },
                {% endfor %}
            ],
            get uniqueSizes() {
                const sizes = this.packages.map(p => p.account_size);
                return [...new Set(sizes)].sort((a, b) => a - b);
            },
            get currentPkg() {
                let pkg = this.packages.find(p => p.model_type === this.activeModel && p.account_size === this.activeSize);
                if (!pkg) {
                    pkg = this.packages.find(p => p.model_type === this.activeModel);
                    if (pkg) this.activeSize = pkg.account_size;
                }
                return pkg || null;
            },
            formatK(val) {
                if (val >= 1000) {
                    return '?' + (val / 1000) + 'K';
                }
                return '?' + val;
            }
        }
    }
</script>
</body>
"""
new_text = new_text.replace('</body>', script_html)

with open('app/templates/landing.html', 'w', encoding='utf-8') as f:
    f.write(new_text)

print('Updated landing.html with FundedFirm pricing section!')

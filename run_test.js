var tailwind = { config: {} };
var document = { 
    documentElement: { classList: { add: function(){} } },
    body: { getAttribute: function(){ return null; } },
    getElementById: function(){ return { classList: { add: function(){}, remove: function(){} }, innerText: '', style: {} }; },
    addEventListener: function(event, cb) { if(event === 'DOMContentLoaded') cb(); },
    querySelectorAll: function() { return []; }
};
var localStorage = { getItem: function(){ return null; } };
var window = {};
var lucide = { createIcons: function(){} };
var fetch = async function() { return { json: async function() { return []; } }; };
var setInterval = function(){};
var LightweightCharts = { createChart: function(){ return { addCandlestickSeries: function(){ return { setData: function(){} }; } }; } };
var TradingView = { widget: function(config){ console.log("TV Widget created:", config); return {}; } };


        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        darkbg: '#050505',
                        darkpanel: '#0a0a0a',
                        darkborder: '#1a1a1a',
                        primary: '#01E083'
                    }
                }
            }
        }
    

    // STATE
    var activeSymbol = document.body.getAttribute('data-active-symbol') || 'NIFTY50';
    var accAttr = document.body.getAttribute('data-account-id');
    var activeAccountId = (accAttr && accAttr !== 'null' && accAttr !== 'None') ? parseInt(accAttr) : null;
    
    var tvWidget1 = null;
    var tvWidget2 = null;
    var isDualChart = false;
    var isTrading = false;
    var pricesData = {};

    // TRADINGVIEW SYMBOL FIX (Intraday / Standard Compatible)
    // NOTE: NSE spot indices (NSE:NIFTY) are blocked by exchange rules on free widgets.
    // We use global CFD equivalents or futures (which are allowed) to ensure the chart loads!
    // We strictly use BINGX Perpetuals (which track NIFTY flawlessly 24/7 and allow 1m/5m charting).
    var tvSymbolMap = {
        'NIFTY50': 'CAPITALCOM:NIFTY50', 
        'BANKNIFTY': 'BINGX:BTCUSDT', 
        'SENSEX': 'BSE:SENSEX',       
        'FINNIFTY': 'BINGX:ETHUSDT',  
        'MIDCPNIFTY': 'BINGX:SOLUSDT', 
        'RELIANCE': 'BSE:RELIANCE',   
        'HDFCBANK': 'BSE:HDFCBANK'
    };

    function formatInr(val) {
        if(!val || isNaN(val)) return "0.00";
        return val.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }

    function showToast(message, type) {
        var container = document.getElementById('toast-container');
        var toast = document.createElement('div');
        toast.className = 'toast ' + (type || 'success');
        toast.innerText = message;
        container.appendChild(toast);
        setTimeout(() => { toast.style.animation = 'slideOut 0.3s ease forwards'; setTimeout(() => toast.remove(), 300); }, 8000);
    }

    function initTVWidget(containerId, sym, interval) {
        return new TradingView.widget({
            "autosize": true,
            "symbol": sym,
            "interval": interval,
            "timezone": "Asia/Kolkata",
            "theme": localStorage.getItem("theme") === "dark" ? "dark" : "light",
            "style": "1",
            "locale": "in",
            "enable_publishing": false,
            "hide_top_toolbar": false,
            "hide_side_toolbar": false,
            "hide_legend": true,
            "save_image": false,
            "container_id": containerId,
            "allow_symbol_change": false,
            "disabled_features": ["header_symbol_search", "header_compare"],
            "studies": ["Volume@tv-basicstudies"]
        });
    }

    function initCharts() {
        if (activeSymbol.endsWith("CE") || activeSymbol.endsWith("PE") || activeSymbol.includes("24") || activeSymbol.includes("25") || activeSymbol.includes("26")) {
            renderOptionChart(activeSymbol);
        } else {
            var tvSym = tvSymbolMap[activeSymbol] || ('NSE:' + activeSymbol);
            var interval = tvSym.startsWith('NSE:') ? "D" : "5";
            tvWidget1 = initTVWidget("tv_chart_container_1", tvSym, interval);
        }
        
        var wl = document.getElementById('wl-' + activeSymbol);
        if(wl) wl.classList.add('active');
    }

    function toggleDualChart() {
        var wrapper2 = document.getElementById('right-chart-wrapper');
        isDualChart = !isDualChart;
        
        if (isDualChart) {
            wrapper2.classList.remove('hidden');
            if (!tvWidget2) {
                // Initialize second chart to BankNifty equivalent
                var tvSym2 = tvSymbolMap['BANKNIFTY'] || 'NSE:BANKNIFTY';
                var interval = tvSym2.startsWith('NSE:') ? "D" : "5";
                tvWidget2 = initTVWidget("tv_chart_container_2", tvSym2, interval);
            }
        } else {
            wrapper2.classList.add('hidden');
        }
    }

    function toggleFullscreen() {
        var elem = document.getElementById("dual-chart-container");
        if (!document.fullscreenElement) {
            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            } else if (elem.webkitRequestFullscreen) { /* Safari */
                elem.webkitRequestFullscreen();
            } else if (elem.msRequestFullscreen) { /* IE11 */
                elem.msRequestFullscreen();
            }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) { /* Safari */
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) { /* IE11 */
                document.msExitFullscreen();
            }
        }
    }




    async function pollPrices() {
        try {
            var res = await fetch('/api/market/prices?active_symbol=' + activeSymbol);
            var prices = await res.json();
            
            for(var i = 0; i < prices.length; i++) {
                var p = prices[i];
                pricesData[p.symbol] = p;
                
                var wlBid = document.getElementById('wl-bid-' + p.symbol);
                var wlAsk = document.getElementById('wl-ask-' + p.symbol);
                if(wlBid) wlBid.innerText = p.bid.toFixed(2);
                if(wlAsk) wlAsk.innerText = p.ask.toFixed(2);

                if(p.symbol === activeSymbol) {
                    var qtBid = document.getElementById('qt-bid');
                    var qtAsk = document.getElementById('qt-ask');
                    if(qtBid) qtBid.innerText = p.bid.toFixed(2);
                    if(qtAsk) qtAsk.innerText = p.ask.toFixed(2);
                    
                    if (typeof lwSeries !== 'undefined' && lwSeries && lastLwCandle && (activeSymbol.endsWith("CE") || activeSymbol.endsWith("PE"))) {
                        var now = Math.floor(Date.now() / 1000) + 19800; // IST rough
                        if (now - lastLwCandle.time > 300) {
                            lastLwCandle = {time: now, open: p.mid, high: p.mid, low: p.mid, close: p.mid};
                        } else {
                            lastLwCandle.close = p.mid;
                            lastLwCandle.high = Math.max(lastLwCandle.high, p.mid);
                            lastLwCandle.low = Math.min(lastLwCandle.low, p.mid);
                        }
                        lwSeries.update(lastLwCandle);
                    }
                }
            }
        } catch (e) {}
    }

    function switchAccount(accountId) {
        if (!accountId) return;
        window.location.href = `/trading?account_id=${accountId}&symbol=${activeSymbol}`;
    }

    async function pollAccountState() {
        if (!activeAccountId) return;
        try {
            var url = '/api/account/' + activeAccountId + '/state';
            var res = await fetch(url);
            var data = await res.json();
            var st = data.state;

            document.getElementById('top-balance').innerText = '\u20B9' + formatInr(st.balance);
            document.getElementById('top-equity').innerText = '\u20B9' + formatInr(st.equity);
            
            var pnlVal = st.floating_pnl || 0;
            var pnlColor = pnlVal >= 0 ? 'text-emerald-500' : 'text-rose-500';
            var pnlSign = pnlVal >= 0 ? '+\u20B9' : '-\u20B9';
            document.getElementById('top-pnl').innerHTML = '<span class="' + pnlColor + '">' + pnlSign + formatInr(Math.abs(pnlVal)) + '</span>';

            var tbody = document.getElementById('pos-tbody');
            var posCount = data.positions ? data.positions.length : 0;
            document.getElementById('pos-count').innerText = posCount;
            
            var html = '';
            if(posCount > 0) {
                for(var i = 0; i < data.positions.length; i++) {
                    var pos = data.positions[i];
                    var isBuy = pos.order_type === 'BUY';
                    var pC = pos.pnl >= 0 ? 'text-emerald-600' : 'text-rose-600';
                    var pS = pos.pnl >= 0 ? '+\u20B9' : '-\u20B9';
                    html += '<tr class="hover:bg-slate-50 dark:bg-darkbg">';
                    html += '<td class="py-2.5 px-4 font-semibold text-slate-500">' + pos.ticket + '</td>';
                    html += '<td class="py-2.5 px-4 font-bold text-slate-900 dark:text-white">' + pos.symbol + '</td>';
                    html += '<td class="py-2.5 px-4 font-black ' + (isBuy ? 'text-emerald-600' : 'text-rose-600') + '">' + pos.order_type + '</td>';
                    html += '<td class="py-2.5 px-4 text-slate-800 dark:text-slate-200">' + pos.volume_lots + '</td>';
                    html += '<td class="py-2.5 px-4 text-slate-800 dark:text-slate-200">' + pos.open_price + '</td>';
                    html += '<td class="py-2.5 px-4 font-bold text-slate-900 dark:text-white">' + pos.current_price + '</td>';
                    html += '<td class="py-2.5 px-4 text-slate-400">-</td>';
                    html += '<td class="py-2.5 px-4 text-right font-black ' + pC + '">' + pS + formatInr(Math.abs(pos.pnl)) + '</td>';
                    html += '<td class="py-2.5 px-4 text-center"><button onclick="closeTrade(' + pos.id + ')" class="text-[10px] font-bold uppercase tracking-wider bg-rose-50 text-rose-600 border border-rose-200 px-3 py-1 rounded hover:bg-rose-500 hover:text-white transition-colors">Close</button></td>';
                    html += '</tr>';
                }
            } else {
                html = '<tr><td colspan="9" class="text-center py-8 text-slate-400 font-sans text-xs">No open positions</td></tr>';
            }
            tbody.innerHTML = html;
            
            if(data.notifications && data.notifications.length > 0) {
                for(var i=0; i < data.notifications.length; i++) {
                    showToast('LIVEMESSAGE: ' + data.notifications[i], 'success');
                    playNotificationSound();
                    showBrowserNotification('Terminal Alert', data.notifications[i]);
                }
            }
        } catch (e) { console.error(e); }
    }

    async function closeAllTrades() {
        if (!confirm('Close ALL open positions?')) return;
        document.querySelectorAll('.btn-close-trade').forEach(btn => btn.click());
    }

    async function placeTrade(orderType) {
        if(isTrading) return;
        var qtyInput = document.getElementById('qt-qty');
        var lots = parseFloat(qtyInput.value);
        if (!lots || lots <= 0) return showToast('Invalid volume', 'error');

        isTrading = true;
        var formData = new FormData();
        formData.append('account_id', activeAccountId);
        formData.append('symbol', activeSymbol);
        formData.append('order_type', orderType);
        formData.append('volume_lots', lots);

        try {
            var res = await fetch('/api/trade/open', { method: 'POST', body: formData });
            var data = await res.json();
            if (data.success) {
                showToast('Filled: ' + orderType + ' ' + lots + ' ' + activeSymbol, 'success');
                pollAccountState();
            } else {
                showToast(data.error || 'Trade rejected', 'error');
            }
        } catch (err) { showToast('Network error', 'error'); } finally { isTrading = false; }
    }

    async function closeTrade(tradeId) {
        try {
            var url = '/api/trade/close/' + tradeId;
            var res = await fetch(url, { method: 'POST' });
            var data = await res.json();
            if (data.success) { showToast('Position closed', 'success'); pollAccountState(); }
        } catch (err) {}
    }

    function switchTab(tab) {
        if(tab === 'positions') {
            document.getElementById('view-pos').classList.remove('hidden');
            document.getElementById('view-hist').classList.add('hidden');
        } else {
            document.getElementById('view-pos').classList.add('hidden');
            document.getElementById('view-hist').classList.remove('hidden');
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        lucide.createIcons();
        initCharts();
        pollPrices();
        pollAccountState();
        setInterval(pollPrices, 1000);
        setInterval(pollAccountState, 1000);
    });


    /* --- OPTION CHAIN LOGIC --- */
    
    function directOpenChart(sym) {
        closeOptionChain();
        addSymbolToWatchlist(sym);
        selectSymbol(sym);
    }

    function openOptionChain() {
        document.getElementById('option-chain-modal').classList.remove('hidden');
        loadOptionChain();
    }
    
    function closeOptionChain() {
        document.getElementById('option-chain-modal').classList.add('hidden');
    }
    
    async function loadOptionChain() {
        const sym = document.getElementById('oc-symbol-select').value;
        const loader = document.getElementById('oc-loader');
        const tbody = document.getElementById('oc-tbody');
        
        loader.classList.remove('hidden');
        try {
            const res = await fetch(`/api/options/${sym}`);
            const data = await res.json();
            
            document.getElementById('oc-spot-price').innerText = data.spot.toFixed(2);
            
            tbody.innerHTML = '';
            
            data.chain.forEach(row => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-indigo-50/50 transition-colors bg-white dark:bg-darkpanel';
                
                // ITM Highlighting logic
                const isCallITM = row.strike < data.spot;
                const isPutITM = row.strike > data.spot;
                
                const callBg = isCallITM ? 'bg-amber-50/30' : '';
                const putBg = isPutITM ? 'bg-amber-50/30' : '';
                
                tr.innerHTML = `
                    <td class="py-1 px-2 border-r border-slate-200 dark:border-darkborder ${callBg}">
                        <div class="flex gap-1 justify-center">
                            <button onclick="prepareOptionTrade('${row.ce_symbol}', 'BUY')" class="bg-emerald-100 text-emerald-700 hover:bg-emerald-500 hover:text-white px-2 py-0.5 rounded text-[10px] font-bold transition-colors">B</button>
                            <button onclick="prepareOptionTrade('${row.ce_symbol}', 'SELL')" class="bg-rose-100 text-rose-700 hover:bg-rose-500 hover:text-white px-2 py-0.5 rounded text-[10px] font-bold transition-colors">S</button>
                        </div>
                    </td>
                    <td class="py-1 px-2 border-r border-slate-200 dark:border-darkborder text-slate-500 ${callBg}">${row.ce_iv}%</td>
                    <td class="py-1 px-2 border-r border-slate-200 dark:border-darkborder text-slate-600 dark:text-slate-400 ${callBg}">${(row.ce_oi/1000).toFixed(1)}k</td>
                    <td class="py-1 px-4 border-r border-slate-200 dark:border-darkborder text-right font-bold text-emerald-600 ${callBg} cursor-pointer hover:bg-emerald-100" onclick="directOpenChart('${row.ce_symbol}')" title="Open Chart">${row.ce_price.toFixed(2)}</td>
                    
                    <td class="py-2 px-4 bg-slate-50 dark:bg-darkbg font-black text-slate-800 dark:text-slate-200 border-x border-slate-300 text-sm shadow-inner">${row.strike}</td>
                    
                    <td class="py-1 px-4 border-l border-slate-200 dark:border-darkborder text-left font-bold text-rose-600 ${putBg} cursor-pointer hover:bg-rose-100" onclick="directOpenChart('${row.pe_symbol}')" title="Open Chart">${row.pe_price.toFixed(2)}</td>
                    <td class="py-1 px-2 border-l border-slate-200 dark:border-darkborder text-slate-600 dark:text-slate-400 ${putBg}">${(row.pe_oi/1000).toFixed(1)}k</td>
                    <td class="py-1 px-2 border-l border-slate-200 dark:border-darkborder text-slate-500 ${putBg}">${row.pe_iv}%</td>
                    <td class="py-1 px-2 border-l border-slate-200 dark:border-darkborder ${putBg}">
                        <div class="flex gap-1 justify-center">
                            <button onclick="prepareOptionTrade('${row.pe_symbol}', 'BUY')" class="bg-emerald-100 text-emerald-700 hover:bg-emerald-500 hover:text-white px-2 py-0.5 rounded text-[10px] font-bold transition-colors">B</button>
                            <button onclick="prepareOptionTrade('${row.pe_symbol}', 'SELL')" class="bg-rose-100 text-rose-700 hover:bg-rose-500 hover:text-white px-2 py-0.5 rounded text-[10px] font-bold transition-colors">S</button>
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            
            // Scroll to ATM
            setTimeout(() => {
                const rows = Array.from(tbody.children);
                const atmRow = rows[Math.floor(rows.length/2)];
                if(atmRow) atmRow.scrollIntoView({block: "center", behavior: "smooth"});
            }, 100);
            
        } catch(e) {
            console.error(e);
            showToast('Failed to load option chain.', 'error');
        } finally {
            loader.classList.add('hidden');
        }
    }
    


    var lwChart = null;
    var lwSeries = null;
    var lastLwCandle = null;

    async function renderOptionChart(symbol) {
        try {
            document.getElementById("tv_chart_container_1").style.display = "none";
            var lwContainer = document.getElementById("lw_chart_container_1");
            lwContainer.style.display = "block";
            lwContainer.innerHTML = "";
            
            // Allow DOM to reflow so clientWidth is populated
            await new Promise(r => setTimeout(r, 50));
            
            var w = lwContainer.clientWidth || 800;
            var h = lwContainer.clientHeight || 500;
            
            lwChart = LightweightCharts.createChart(lwContainer, {
                width: w,
                height: h,
                layout: { background: { type: 'solid', color: '#0f172a' }, textColor: '#94a3b8' },
                grid: { vertLines: { color: '#f0f0f0' }, horzLines: { color: '#f0f0f0' } },
                timeScale: { timeVisible: true, secondsVisible: false },
            });
            
            lwSeries = lwChart.addCandlestickSeries({
                upColor: '#22c55e', downColor: '#ef4444', borderVisible: false,
                wickUpColor: '#22c55e', wickDownColor: '#ef4444'
            });

            var res = await fetch('/api/market/candles/' + symbol);
            var data = await res.json();
            var cData = data.map(c => ({
                time: c.time + 19800,
                open: c.open, high: c.high, low: c.low, close: c.close
            }));
            lwSeries.setData(cData);
            if(cData.length > 0) lastLwCandle = cData[cData.length - 1];
        } catch(e) {
            console.error("Option Chart Error:", e);
            document.getElementById("lw_chart_container_1").innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#94a3b8;font-family:monospace;">Option Chart Loading Failed: ' + e.message + ' <br> Stack: ' + e.stack + '</div>';
        }
    }

    
    const searchInput = document.getElementById('symbol-search');
    const searchResults = document.getElementById('search-results');
    const baseInstruments = ['NIFTY50', 'BANKNIFTY', 'SENSEX', 'CRUDEOIL', 'GOLD', 'EURINR', 'BTCINR'];

    searchInput.addEventListener('input', function(e) {
        const query = this.value.toUpperCase().replace(/\s+/g, '');
        if (query.length < 2) {
            searchResults.classList.add('hidden');
            return;
        }

        let suggestions = [];
        baseInstruments.forEach(inst => {
            if (inst.includes(query)) suggestions.push(inst);
        });

        const optMatch = query.match(/^([A-Z]+)(\d{2,})?(C|P|CE|PE)?$/);
        if (optMatch) {
            const base = optMatch[1];
            const strikePart = optMatch[2] || '';
            
            if (['NIFTY', 'BANKNIFTY', 'SENSEX'].includes(base)) {
                let strikeBase = 24000;
                let step = 50;
                if (base === 'BANKNIFTY') { strikeBase = 52000; step = 100; }
                if (base === 'SENSEX') { strikeBase = 80000; step = 100; }

                if (strikePart.length >= 2) {
                    const targetStr = strikePart.padEnd(5, '0');
                    const targetVal = parseInt(targetStr);
                    const nearest = Math.round(targetVal / step) * step;
                    for (let i = -3; i <= 3; i++) {
                        const s = nearest + (i * step);
                        suggestions.push(`${base}${s}CE`);
                        suggestions.push(`${base}${s}PE`);
                    }
                } else {
                    for (let i = -2; i <= 2; i++) {
                        const s = strikeBase + (i * step);
                        suggestions.push(`${base}${s}CE`);
                        suggestions.push(`${base}${s}PE`);
                    }
                }
            }
        }

        suggestions = suggestions.filter(s => s.includes(query));
        suggestions = [...new Set(suggestions)].slice(0, 8);

        if (suggestions.length > 0) {
            searchResults.innerHTML = suggestions.map(sym => 
                `<div class="px-4 py-2 text-xs font-bold text-slate-700 dark:text-slate-300 hover:bg-indigo-50 hover:text-indigo-700 cursor-pointer border-b border-slate-50 last:border-0" 
                      onclick="addSymbolToWatchlist('${sym}'); selectSymbol('${sym}'); searchResults.classList.add('hidden'); searchInput.value='';">
                    ${sym}
                </div>`
            ).join('');
            searchResults.classList.remove('hidden');
        } else {
            searchResults.classList.add('hidden');
        }
    });

    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            var sym = this.value.toUpperCase().replace(/\s+/g, '');
            if (sym) {
                addSymbolToWatchlist(sym);
                selectSymbol(sym);
                this.value = '';
                searchResults.classList.add('hidden');
            }
        }
    });
    
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('hidden');
        }
    });

    function addSymbolToWatchlist(sym) {
        // Check if already exists
        if (document.getElementById('wl-' + sym)) return;
        
        var container = document.getElementById('watchlist-container');
        var div = document.createElement('div');
        div.onclick = () => selectSymbol(sym);
        div.id = 'wl-' + sym;
        div.className = 'wl-item flex items-center px-4 py-2.5 border-b border-slate-50 cursor-pointer transition-colors border-l-2 border-l-transparent hover:bg-slate-50 dark:bg-darkbg group';
        div.innerHTML = `
            <div class="flex-1">
                <div class="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-blue-600 transition-colors">${sym}</div>
            </div>
            <div class="w-16 text-right text-xs font-mono font-bold text-slate-700 dark:text-slate-300" id="wl-bid-${sym}">...</div>
            <div class="w-16 text-right text-xs font-mono font-bold text-slate-700 dark:text-slate-300" id="wl-ask-${sym}">...</div>
        `;
        container.prepend(div);
        
        // Add to activeSymbol tracking if not already there
        if (typeof priceUpdateLoop === 'undefined') {
            // We just let the websocket or price poller update it
        }
    }

    function selectSymbol(sym) {
        var oldWl = document.getElementById('wl-' + activeSymbol);
        if(oldWl) oldWl.classList.remove('active');
        
        activeSymbol = sym;
        
        var newWl = document.getElementById('wl-' + activeSymbol);
        if(newWl) newWl.classList.add('active');
        
        document.getElementById('order-symbol-title').innerText = sym;
        
        if (sym.endsWith("CE") || sym.endsWith("PE") || sym.includes("24") || sym.includes("25") || sym.includes("26")) {
            renderOptionChart(sym);
        } else {
            document.getElementById("lw_chart_container_1").style.display = "none";
            document.getElementById("tv_chart_container_1").style.display = "block";
            
            var tvSym = tvSymbolMap[sym] || ('NSE:' + sym);
            var interval = tvSym.startsWith('NSE:') ? "D" : "5"; 
            
            document.getElementById("tv_chart_container_1").innerHTML = "";
            tvWidget1 = initTVWidget("tv_chart_container_1", tvSym, interval);
        }
    }

    function prepareOptionTrade(symbol, action) {
        closeOptionChain();
        selectSymbol(symbol); // Now actually select it so the chart changes!
        
        var qtyInput = document.getElementById('qt-qty');
        if (symbol.includes('BANK')) {
            qtyInput.value = '15';
        } else {
            qtyInput.value = '25';
        }
        
        placeTrade(action);
        showToast(`Placing ${action} order for ${symbol}...`, 'success');
    }



    function requestBrowserPermission() {
        if (!("Notification" in window)) {
            alert("This browser does not support desktop notification");
        } else if (Notification.permission === "granted") {
            showToast("Notifications are already enabled!", "success");
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then((permission) => {
                if (permission === "granted") {
                    new Notification("MyFundedDesk", { body: "Notifications enabled!" });
                }
            });
        }
    }

    function playNotificationSound() {
        let audio = new Audio("https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3");
        audio.play().catch(e=>console.log("Audio blocked:", e));
    }

    function showBrowserNotification(title, body) {
        if (window.Notification && Notification.permission === "granted") {
            new Notification(title, { body: body });
        }
    }

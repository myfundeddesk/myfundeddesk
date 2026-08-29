with open("app/templates/base.html", "r", encoding="utf-8") as f:
    text = f.read()

start_marker = "<!-- Notifications -->"
end_marker = "<!-- Profile Dropdown -->"

start = text.find(start_marker)
end = text.find(end_marker, start)

new_block = """<!-- Notifications -->
    <div class="relative" x-data="{ openNotifs: false, notifs: [], unreadCount: 0 }" x-init="
        fetch('/api/notifications').then(r => r.json()).then(d => { 
            notifs = d; 
            unreadCount = d.length; 
        }).catch(e => console.log(e));
        setInterval(() => {
            fetch('/api/notifications').then(r => r.json()).then(d => { 
                const newNotifs = d.filter(n => !notifs.some(old => old.id === n.id));
                if (newNotifs.length > 0) {
                    
                    let audio = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3');
                    audio.play().catch(e=>console.log('Audio blocked:', e));
                    
                    newNotifs.forEach(n => {
                        // Native OS Push Notification
                        if (Notification.permission === 'granted') {
                            new Notification('MyFundedDesk Alert', { body: n.message });
                        }

                        // Show Toast Notification
                        const toast = document.createElement('div');
                        toast.className = 'bg-slate-900 border border-slate-700 text-white px-4 py-3 rounded-lg shadow-xl mb-2 transform transition-all duration-300 translate-x-full';
                        toast.innerHTML = `<div class='font-bold text-sm flex items-center gap-2'><i data-lucide='bell' class='w-4 h-4 text-primary'></i> New Alert</div><div class='text-xs text-slate-300 mt-1'>${n.message}</div>`;
                        document.getElementById('toast-container').appendChild(toast);
                        lucide.createIcons({ root: toast });
                        setTimeout(() => toast.style.transform = 'translateX(0)', 10);
                        setTimeout(() => {
                            toast.style.opacity = '0';
                            setTimeout(() => toast.remove(), 300);
                        }, 5000);
                    });
                }
                notifs = d; 
                unreadCount = d.length; 
            }).catch(e => console.log(e));
        }, 5000);
    ">
        <button @click="openNotifs = !openNotifs; if(Notification.permission === 'default') Notification.requestPermission();" class="p-2 text-slate-400 dark:text-slate-500 hover:bg-slate-100 dark:hover:bg-white/5 rounded-full transition-colors relative block">
            <i data-lucide="bell" class="w-5 h-5"></i>
            <span x-show="unreadCount > 0" x-text="unreadCount" class="absolute top-0 right-0 w-4 h-4 bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center rounded-full border border-white dark:border-darkpanel"></span>
        </button>
        
        <div x-show="openNotifs" @click.away="openNotifs = false" class="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl py-2 z-50 max-h-[400px] flex flex-col" style="display: none;">
            <div class="px-4 py-3 border-b border-slate-100 dark:border-slate-800 font-bold text-slate-800 dark:text-white flex justify-between items-center">
                <span>Platform Notifications</span>
                <span class="text-[10px] bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-slate-500" x-text="Notification.permission === 'granted' ? 'Push Enabled' : 'Push Disabled'"></span>
            </div>
            <div class="overflow-y-auto flex-1 p-2 space-y-2">
                <template x-for="n in notifs" :key="n.id">
                    <div class="p-3 bg-slate-50 dark:bg-slate-800 rounded-xl relative group">
                        <p class="text-sm text-slate-700 dark:text-slate-300 pr-5" x-text="n.message"></p>
                        <span class="text-[10px] text-slate-400 block mt-1" x-text="new Date(n.created_at).toLocaleString()"></span>
                        <button @click="fetch('/api/notifications/'+n.id+'/dismiss', {method: 'POST'}).then(() => { notifs = notifs.filter(x => x.id !== n.id); unreadCount = notifs.length; })" class="absolute top-2 right-2 text-slate-400 hover:text-rose-500 p-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <i data-lucide="x" class="w-4 h-4"></i>
                        </button>
                    </div>
                </template>
                <div x-show="notifs.length === 0" class="text-center text-slate-500 text-sm py-4">No notifications.</div>
            </div>
        </div>
    </div>

                
                """

text = text[:start] + new_block + text[end:]

with open("app/templates/base.html", "w", encoding="utf-8") as f:
    f.write(text)

print("Patched base.html notifications!")

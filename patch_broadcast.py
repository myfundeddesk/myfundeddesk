with open("app/templates/admin_dashboard.html", "r", encoding="utf-8") as f:
    text = f.read()

broadcast_html = """
                            <div class="col-lg-12">
                                <div class="card b-radius--10 mt-4">
                                    <div class="card-header">
                                        <h5 class="card-title mb-0">Push Notification System (Global)</h5>
                                    </div>
                                    <div class="card-body">
                                        <form id="broadcastForm">
                                            <div class="input-group">
                                                <input type="text" id="broadcastMessage" class="form-control" placeholder="Enter message to broadcast to all users (Triggers Web Push & In-App)..." required>
                                                <button type="submit" class="btn btn-primary"><i class="las la-paper-plane"></i> Send Broadcast</button>
                                            </div>
                                        </form>
                                        <div id="broadcastStatus" class="mt-2 text-sm text-success" style="display:none;"></div>
                                    </div>
                                </div>
                            </div>
"""

# Insert it before the last closing </div> of tab-dashboard which I appended charts to.
# Let's just find "Login by Country & Browser" and prepend the broadcast there.
target = '<!-- User Analytics & IP Management -->'
if target in text and "Push Notification System" not in text:
    text = text.replace(target, broadcast_html + '\n                        ' + target)

    script_injection = """
        // Broadcast Form
        document.getElementById('broadcastForm')?.addEventListener('submit', function(e) {
            e.preventDefault();
            const msg = document.getElementById('broadcastMessage').value;
            const formData = new FormData();
            formData.append('entity', 'system');
            formData.append('id', 'all');
            formData.append('action', 'broadcast');
            formData.append('payload', msg);
            
            fetch('/admin/api/action', {
                method: 'POST',
                body: formData
            }).then(r => r.json()).then(d => {
                const stat = document.getElementById('broadcastStatus');
                stat.innerText = "Broadcast Sent Successfully!";
                stat.style.display = "block";
                document.getElementById('broadcastMessage').value = '';
                setTimeout(() => stat.style.display = 'none', 3000);
            });
        });
    """
    
    # inject the script right before </body>
    text = text.replace('</body>', script_injection + '\n</body>')

with open("app/templates/admin_dashboard.html", "w", encoding="utf-8") as f:
    f.write(text)

print("Injected broadcast UI!")

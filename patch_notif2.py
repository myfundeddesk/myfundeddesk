with open("app/templates/base.html", "r", encoding="utf-8") as f:
    text = f.read()

# Replace the simple new Notification with a richer one
old_notif = "new Notification('MyFundedDesk Alert', { body: n.message });"
new_notif = """const notification = new Notification('MyFundedDesk Alert', { 
                                body: n.message,
                                icon: 'https://cdn-icons-png.flaticon.com/512/3649/3649473.png' // Default bell icon
                            });
                            notification.onclick = function() {
                                window.focus();
                                this.close();
                            };"""

if old_notif in text:
    text = text.replace(old_notif, new_notif)
    with open("app/templates/base.html", "w", encoding="utf-8") as f:
        f.write(text)
    print("Upgraded Notification API call to include icon and focus handler.")
else:
    print("Could not find the old notification call.")

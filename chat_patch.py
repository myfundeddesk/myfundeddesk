with open("app/templates/base.html", "r", encoding="utf-8") as f:
    text = f.read()

chat_snippet = """
<!--Start of Tawk.to Script-->
<script type="text/javascript">
var Tawk_API=Tawk_API||{}, Tawk_LoadStart=new Date();
(function(){
var s1=document.createElement("script"),s0=document.getElementsByTagName("script")[0];
s1.async=true;
s1.src='https://embed.tawk.to/67890abcdef/123456789';
s1.charset='UTF-8';
s1.setAttribute('crossorigin','*');
s0.parentNode.insertBefore(s1,s0);
})();
</script>
<!--End of Tawk.to Script-->
"""

if "Tawk.to Script" not in text:
    text = text.replace("</body>", chat_snippet + "\n</body>")
    with open("app/templates/base.html", "w", encoding="utf-8") as f:
        f.write(text)
    print("Injected chat script into base.html")
else:
    print("Chat script already in base.html")

with open("app/templates/admin_dashboard.html", "r", encoding="utf-8") as f:
    admin_text = f.read()

if "Tawk.to Script" not in admin_text:
    admin_text = admin_text.replace("</body>", chat_snippet + "\n</body>")
    with open("app/templates/admin_dashboard.html", "w", encoding="utf-8") as f:
        f.write(admin_text)
    print("Injected chat script into admin_dashboard.html")

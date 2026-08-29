with open("app/templates/admin_dashboard.html", "r", encoding="utf-8") as f:
    text = f.read()

script_injection = """
    <!-- TinyMCE (WordPress Style Editor) -->
    <script src="https://cdn.tiny.cloud/1/no-api-key/tinymce/6/tinymce.min.js" referrerpolicy="origin"></script>
    <script>
      document.addEventListener("DOMContentLoaded", function() {
          if(typeof tinymce !== 'undefined') {
              tinymce.init({
                selector: '#content',
                plugins: 'preview importcss searchreplace autolink autosave save directionality code visualblocks visualchars fullscreen image link media template codesample table charmap pagebreak nonbreaking anchor insertdatetime advlist lists wordcount help charmap quickbars emoticons',
                menubar: 'file edit view insert format tools table help',
                toolbar: 'undo redo | bold italic underline strikethrough | fontfamily fontsize blocks | alignleft aligncenter alignright alignjustify | outdent indent |  numlist bullist | forecolor backcolor removeformat | pagebreak | charmap emoticons | fullscreen  preview save print | insertfile image media template link anchor codesample | ltr rtl',
                toolbar_sticky: true,
                skin: 'oxide-dark',
                content_css: 'dark',
                height: 500,
                quickbars_selection_toolbar: 'bold italic | quicklink h2 h3 blockquote quickimage quicktable',
                noneditable_class: 'mceNonEditable',
                toolbar_mode: 'sliding',
                contextmenu: 'link image table',
              });
          }
      });
    </script>
"""

if "tinymce.min.js" not in text:
    text = text.replace("</body>", script_injection + "\n</body>")
    with open("app/templates/admin_dashboard.html", "w", encoding="utf-8") as f:
        f.write(text)
    print("Injected TinyMCE")
else:
    print("TinyMCE already there")

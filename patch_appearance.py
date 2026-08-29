with open("app/templates/admin_dashboard.html", "r", encoding="utf-8") as f:
    text = f.read()

sidebar_addition = """
                        <!-- Appearance (WordPress Style) -->
                        <li class="sidebar-menu-item sidebar-dropdown">
                            <a href="javascript:void(0)" class="nav-link">
                                <i class="menu-icon las la-paint-brush"></i>
                                <span class="menu-title">Appearance</span>
                            </a>
                            <div class="sidebar-submenu">
                                <ul>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('customizer', this)"><i class="menu-icon las la-magic"></i><span class="menu-title">Landing Customizer</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('customizer', this)"><i class="menu-icon las la-bars"></i><span class="menu-title">Menus</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('customizer', this)"><i class="menu-icon las la-border-all"></i><span class="menu-title">Widgets</span></a></li>
                                </ul>
                            </div>
                        </li>
"""

if "la-paint-brush" not in text:
    target = '<li class="sidebar-menu-item mt-5">'
    text = text.replace(target, sidebar_addition + '\n                        ' + target)
    with open("app/templates/admin_dashboard.html", "w", encoding="utf-8") as f:
        f.write(text)
    print("Added Appearance menu to sidebar")

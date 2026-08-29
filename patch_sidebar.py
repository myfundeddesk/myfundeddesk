with open('app/templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

start_sidebar = text.find('<ul class="sidebar__menu">')
end_sidebar = text.find('</ul>', start_sidebar) + 5

sidebar_html = """<ul class="sidebar__menu">
                        <li class="sidebar-menu-item active">
                            <a href="#" class="nav-link" onclick="switchTab('dashboard', this)">
                                <i class="menu-icon las la-home"></i>
                                <span class="menu-title">Dashboard</span>
                            </a>
                        </li>
                        <li class="sidebar-menu-item">
                            <a href="#" class="nav-link" onclick="switchTab('users', this)">
                                <i class="menu-icon las la-users"></i>
                                <span class="menu-title">Manage Users</span>
                            </a>
                        </li>
                        <li class="sidebar-menu-item">
                            <a href="#" class="nav-link" onclick="switchTab('accounts', this)">
                                <i class="menu-icon las la-id-card"></i>
                                <span class="menu-title">Trade Accounts</span>
                            </a>
                        </li>
                        <li class="sidebar-menu-item">
                            <a href="#" class="nav-link" onclick="switchTab('trades', this)">
                                <i class="menu-icon las la-coins"></i>
                                <span class="menu-title">Manage Orders</span>
                            </a>
                        </li>
                        
                        <!-- Deposits Dropdown -->
                        <li class="sidebar-menu-item sidebar-dropdown">
                            <a href="javascript:void(0)" class="nav-link">
                                <i class="menu-icon las la-file-invoice-dollar"></i>
                                <span class="menu-title">Deposits</span>
                                <span class="menu-badge bg--warning ms-auto"><i class="las la-exclamation"></i></span>
                            </a>
                            <div class="sidebar-submenu">
                                <ul>
                                    <li class="sidebar-menu-item">
                                        <a href="#" class="nav-link" onclick="switchTab('deposits', this)">
                                            <i class="menu-icon las la-dot-circle"></i>
                                            <span class="menu-title">Pending Deposits</span>
                                            <span class="menu-badge bg--info ms-auto">149</span>
                                        </a>
                                    </li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('deposits', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Approved Deposits</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('deposits', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Successful Deposits</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('deposits', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Rejected Deposits</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('deposits', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Initiated Deposits</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('deposits', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">All Deposits</span></a></li>
                                </ul>
                            </div>
                        </li>

                        <!-- Withdrawals Dropdown -->
                        <li class="sidebar-menu-item sidebar-dropdown">
                            <a href="javascript:void(0)" class="nav-link">
                                <i class="menu-icon las la-university"></i>
                                <span class="menu-title">Withdrawals</span>
                                <span class="menu-badge bg--warning ms-auto"><i class="las la-exclamation"></i></span>
                            </a>
                            <div class="sidebar-submenu">
                                <ul>
                                    <li class="sidebar-menu-item">
                                        <a href="#" class="nav-link" onclick="switchTab('withdrawals', this)">
                                            <i class="menu-icon las la-dot-circle"></i>
                                            <span class="menu-title">Pending Withdrawals</span>
                                            <span class="menu-badge bg--info ms-auto">9</span>
                                        </a>
                                    </li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('withdrawals', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Approved Withdrawals</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('withdrawals', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Rejected Withdrawals</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('withdrawals', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">All Withdrawals</span></a></li>
                                </ul>
                            </div>
                        </li>

                        <!-- Support Ticket Dropdown -->
                        <li class="sidebar-menu-item sidebar-dropdown">
                            <a href="javascript:void(0)" class="nav-link">
                                <i class="menu-icon las la-ticket-alt"></i>
                                <span class="menu-title">Support Ticket</span>
                                <span class="menu-badge bg--warning ms-auto"><i class="las la-exclamation"></i></span>
                            </a>
                            <div class="sidebar-submenu">
                                <ul>
                                    <li class="sidebar-menu-item">
                                        <a href="#" class="nav-link" onclick="switchTab('support', this)">
                                            <i class="menu-icon las la-dot-circle"></i>
                                            <span class="menu-title">Pending Ticket</span>
                                            <span class="menu-badge bg--info ms-auto">57</span>
                                        </a>
                                    </li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('support', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Closed Ticket</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('support', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Answered Ticket</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('support', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">All Ticket</span></a></li>
                                </ul>
                            </div>
                        </li>

                        <!-- Report Dropdown -->
                        <li class="sidebar-menu-item sidebar-dropdown">
                            <a href="javascript:void(0)" class="nav-link">
                                <i class="menu-icon las la-list"></i>
                                <span class="menu-title">Report</span>
                            </a>
                            <div class="sidebar-submenu">
                                <ul>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('reports', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Transaction History</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('reports', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Login History</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('reports', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Notification History</span></a></li>
                                </ul>
                            </div>
                        </li>

                        <li class="sidebar-menu-item">
                            <a href="#" class="nav-link" onclick="switchTab('subscribers', this)">
                                <i class="menu-icon las la-thumbs-up"></i>
                                <span class="menu-title">Subscribers</span>
                            </a>
                        </li>

                        <li class="sidebar-menu-item">
                            <a href="#" class="nav-link" onclick="switchTab('packages', this)">
                                <i class="menu-icon las la-signal"></i>
                                <span class="menu-title">Manage Plans</span>
                            </a>
                        </li>
                        <li class="sidebar-menu-item">
                            <a href="#" class="nav-link" onclick="switchTab('pages', this)">
                                <i class="menu-icon las la-file-alt"></i>
                                <span class="menu-title">Manage Pages</span>
                            </a>
                        </li>
                        <li class="sidebar-menu-item">
                            <a href="#" class="nav-link" onclick="switchTab('settings', this)">
                                <i class="menu-icon las la-life-ring"></i>
                                <span class="menu-title">System Setting</span>
                            </a>
                        </li>

                        <!-- Extra Dropdown -->
                        <li class="sidebar-menu-item sidebar-dropdown">
                            <a href="javascript:void(0)" class="nav-link">
                                <i class="menu-icon las la-server"></i>
                                <span class="menu-title">Extra</span>
                            </a>
                            <div class="sidebar-submenu">
                                <ul>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('extra', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Application</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('extra', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Server</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('extra', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Cache</span></a></li>
                                    <li class="sidebar-menu-item"><a href="#" class="nav-link" onclick="switchTab('extra', this)"><i class="menu-icon las la-dot-circle"></i><span class="menu-title">Update</span></a></li>
                                </ul>
                            </div>
                        </li>

                        <li class="sidebar-menu-item mt-5">
                            <a href="/trading" target="_blank" class="nav-link">
                                <i class="menu-icon las la-globe"></i>
                                <span class="menu-title">Visit Terminal</span>
                            </a>
                        </li>
                    </ul>"""

new_text = text[:start_sidebar] + sidebar_html + text[end_sidebar:]

# Add JS for sidebar dropdown functionality since it might be missing if I stripped it
js_sidebar = """
        // Sidebar Dropdown
        $('.sidebar-dropdown > a').on('click', function () {
            var submenu = $(this).siblings('.sidebar-submenu');
            if (submenu.length > 0) {
                submenu.slideToggle();
                $(this).parent().toggleClass('active');
            }
        });
"""
if "Sidebar Dropdown" not in new_text:
    new_text = new_text.replace('// Fix toggling sidebar for responsive design', js_sidebar + '\n        // Fix toggling sidebar for responsive design')

with open('app/templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(new_text)

print("Patched admin_dashboard.html sidebar!")

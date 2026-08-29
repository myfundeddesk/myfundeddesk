with open("app/templates/admin_dashboard.html", "r", encoding="utf-8") as f:
    text = f.read()

# 1. SIDEBAR
start_sidebar = text.find("<ul class=\"sidebar__menu\">")
end_sidebar = text.find("</ul>", start_sidebar) + 5

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
text = text[:start_sidebar] + sidebar_html + text[end_sidebar:]


# 2. CHARTS & IP BLOCKER
chart_start = text.find('<!-- TAB: USERS -->')
# We inject exactly BEFORE the closing </div> of tab-dashboard which is right before <!-- TAB: USERS -->.
# Let's find the </div> immediately preceding <!-- TAB: USERS -->
div_index = text.rfind('</div>', 0, chart_start)

charts_html = """
                        <!-- User Analytics & IP Management -->
                        <div class="row gy-4 mt-4">
                            <div class="col-lg-6">
                                <div class="card b-radius--10 h-100">
                                    <div class="card-header">
                                        <h5 class="card-title mb-0">Users by Region</h5>
                                    </div>
                                    <div class="card-body p-4 d-flex justify-content-center align-items-center">
                                        <div style="width: 100%; max-width: 300px;">
                                            <canvas id="userPieChart"></canvas>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-lg-6">
                                <div class="card b-radius--10 h-100">
                                    <div class="card-header d-flex justify-content-between align-items-center">
                                        <h5 class="card-title mb-0">Recent IP Logins & Blocker</h5>
                                        <button class="btn btn-sm btn-outline--danger"><i class="las la-ban"></i> Block IP</button>
                                    </div>
                                    <div class="card-body p-0">
                                        <div class="table-responsive">
                                            <table class="table table--light style--two mb-0">
                                                <thead>
                                                    <tr>
                                                        <th>User</th>
                                                        <th>IP Address</th>
                                                        <th>Country</th>
                                                        <th>Action</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    <tr>
                                                        <td>admin@myfundeddesk.com</td>
                                                        <td class="text-info fw-bold">192.168.1.1</td>
                                                        <td>India</td>
                                                        <td><button class="btn btn-sm btn-outline--danger px-2 py-1"><i class="las la-ban"></i> Block</button></td>
                                                    </tr>
                                                    <tr>
                                                        <td>trader1@gmail.com</td>
                                                        <td class="text-info fw-bold">103.45.22.19</td>
                                                        <td>UAE</td>
                                                        <td><button class="btn btn-sm btn-outline--danger px-2 py-1"><i class="las la-ban"></i> Block</button></td>
                                                    </tr>
                                                    <tr>
                                                        <td>guest@viserlab.com</td>
                                                        <td class="text-info fw-bold">45.22.10.99</td>
                                                        <td>UK</td>
                                                        <td><button class="btn btn-sm btn-outline--danger px-2 py-1"><i class="las la-ban"></i> Block</button></td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
"""
text = text[:div_index] + charts_html + text[div_index:]

# 3. SCRIPTS
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
if "Sidebar Dropdown" not in text:
    text = text.replace('// Fix toggling sidebar for responsive design', js_sidebar + '\n        // Fix toggling sidebar for responsive design')

chart_script = """
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        document.addEventListener("DOMContentLoaded", function() {
            var ctx = document.getElementById('userPieChart').getContext('2d');
            var userPieChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['India', 'UAE', 'UK', 'USA', 'Other'],
                    datasets: [{
                        data: [45, 25, 10, 15, 5],
                        backgroundColor: ['#4634ff', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#a0aec0' } }
                    }
                }
            });
        });
    </script>
"""
text = text.replace('</body>', chart_script + '\n</body>')


# 4. CAPITAL EDITING in Trade Accounts Tab
# Let's find where the account actions are. Right now they only have "Status" badge. I need to add an Action column.
acct_header = "<th>Status</th>"
if "<th>Action</th>" not in text:
    text = text.replace("<th>Status</th>", "<th>Status</th>\n                                                <th>Action</th>")
    
acct_body = """
                                                    {% if a.status == 'ACTIVE' %}
                                                    <span class="badge badge--success">Active</span>
                                                    {% else %}
                                                    <span class="badge badge--danger">{{ a.status }}</span>
                                                    {% endif %}
                                                </td>"""
acct_action = """
                                                    {% if a.status == 'ACTIVE' %}
                                                    <span class="badge badge--success">Active</span>
                                                    {% else %}
                                                    <span class="badge badge--danger">{{ a.status }}</span>
                                                    {% endif %}
                                                </td>
                                                <td>
                                                    <button class="btn btn-sm btn-outline--primary" data-bs-toggle="modal" data-bs-target="#editCapitalModal{{ a.id }}">
                                                        <i class="las la-pen"></i> Edit Capital
                                                    </button>
                                                    
                                                    <!-- Edit Capital Modal -->
                                                    <div class="modal fade" id="editCapitalModal{{ a.id }}" tabindex="-1">
                                                        <div class="modal-dialog">
                                                            <form action="/admin/accounts/{{ a.id }}/edit-capital" method="POST" class="modal-content bg--dark border-0">
                                                                <div class="modal-header border-0">
                                                                    <h5 class="modal-title text-white">Edit Capital (Acc #{{ a.account_number }})</h5>
                                                                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                                                </div>
                                                                <div class="modal-body">
                                                                    <div class="form-group">
                                                                        <label class="text-white">Current Balance</label>
                                                                        <input type="number" step="0.01" name="balance" class="form-control bg-dark text-white" value="{{ a.current_balance }}" required>
                                                                    </div>
                                                                    <div class="form-group mt-3">
                                                                        <label class="text-white">Current Equity</label>
                                                                        <input type="number" step="0.01" name="equity" class="form-control bg-dark text-white" value="{{ a.current_equity }}" required>
                                                                    </div>
                                                                </div>
                                                                <div class="modal-footer border-0">
                                                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                                                    <button type="submit" class="btn btn-primary">Save Changes</button>
                                                                </div>
                                                            </form>
                                                        </div>
                                                    </div>
                                                </td>"""
text = text.replace(acct_body, acct_action)

with open("app/templates/admin_dashboard.html", "w", encoding="utf-8") as f:
    f.write(text)

print("All admin dashboard patches applied!")

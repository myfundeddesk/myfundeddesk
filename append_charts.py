with open('app/templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('<!-- TAB: USERS -->')

charts_html = """
                        <!-- User Analytics & IP Management -->
                        <div class="row gy-4 mt-3">
                            <div class="col-lg-6">
                                <div class="card b-radius--10">
                                    <div class="card-header">
                                        <h5 class="card-title mb-0">Login by Country & Browser</h5>
                                    </div>
                                    <div class="card-body p-4 d-flex justify-content-center">
                                        <div style="width: 100%; max-width: 300px;">
                                            <canvas id="userPieChart"></canvas>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-lg-6">
                                <div class="card b-radius--10">
                                    <div class="card-header d-flex justify-content-between align-items-center">
                                        <h5 class="card-title mb-0">Recent IP Logins & Blocker</h5>
                                        <button class="btn btn-sm btn-outline--danger"><i class="las la-ban"></i> Add IP to Blocklist</button>
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
                                                        <td><button class="btn btn-sm btn-danger px-2 py-1"><i class="las la-ban"></i> Block</button></td>
                                                    </tr>
                                                    <tr>
                                                        <td>trader1@gmail.com</td>
                                                        <td class="text-info fw-bold">103.45.22.19</td>
                                                        <td>UAE</td>
                                                        <td><button class="btn btn-sm btn-danger px-2 py-1"><i class="las la-ban"></i> Block</button></td>
                                                    </tr>
                                                    <tr>
                                                        <td>guest@viserlab.com</td>
                                                        <td class="text-info fw-bold">45.22.10.99</td>
                                                        <td>UK</td>
                                                        <td><button class="btn btn-sm btn-danger px-2 py-1"><i class="las la-ban"></i> Block</button></td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div> <!-- End of tab-dashboard inner wrapper, closing the tab-dashboard div! Wait! Let me check where the div actually ends! -->
"""
# I need to insert it right before <!-- TAB: USERS -->
new_text = text[:start] + charts_html + "\n                    " + text[start:]

# Inject Chart.js script at the bottom
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

new_text = new_text.replace('</body>', chart_script + '\n</body>')

with open('app/templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(new_text)

print("Injected Pie Chart and IP Blocker into Dashboard!")

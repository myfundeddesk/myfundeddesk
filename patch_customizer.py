with open("app/templates/admin_dashboard.html", "r", encoding="utf-8") as f:
    text = f.read()

customizer_html = """
                    <!-- TAB: CUSTOMIZER (WordPress Style) -->
                    <div id="tab-customizer" class="admin-tab" style="display: none;">
                        <div class="row">
                            <div class="col-xl-12">
                                <div class="card b-radius--10 mb-4">
                                    <div class="card-header d-flex justify-content-between align-items-center">
                                        <h5><i class="las la-paint-brush"></i> WordPress-Style Landing Page Customizer</h5>
                                    </div>
                                    <div class="card-body">
                                        <form action="/admin/api/customize" method="POST">
                                            <div class="row">
                                                <div class="col-md-6 mb-4">
                                                    <div class="form-group">
                                                        <label class="fw-bold">Hero Title (Line 1)</label>
                                                        <input type="text" class="form-control" name="hero_title_1" value="Built for Traders." placeholder="e.g. Built for Traders.">
                                                    </div>
                                                </div>
                                                <div class="col-md-6 mb-4">
                                                    <div class="form-group">
                                                        <label class="fw-bold">Hero Title (Line 2 Highlighted)</label>
                                                        <input type="text" class="form-control" name="hero_title_2" value="Funded by Us." placeholder="e.g. Funded by Us.">
                                                    </div>
                                                </div>
                                                <div class="col-md-12 mb-4">
                                                    <div class="form-group">
                                                        <label class="fw-bold">Hero Subtitle</label>
                                                        <textarea class="form-control" name="hero_subtitle" rows="3" placeholder="We provide up to ?1,00,00,000 in real capital...">We provide up to ?1,00,00,000 in real capital. You keep 90% of the profits. No hidden rules. No excuses. Just pure trading.</textarea>
                                                    </div>
                                                </div>
                                                <div class="col-md-6 mb-4">
                                                    <div class="form-group">
                                                        <label class="fw-bold">Primary Brand Color (Hex)</label>
                                                        <div class="input-group">
                                                            <span class="input-group-text" style="background-color: #10b981; border:none;"></span>
                                                            <input type="text" class="form-control" name="primary_color" value="#10b981">
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="col-md-6 mb-4">
                                                    <div class="form-group">
                                                        <label class="fw-bold">Top Announcement Bar Text</label>
                                                        <input type="text" class="form-control" name="announcement_text" value="?? Update 2.0: 100k Instant account">
                                                    </div>
                                                </div>
                                                
                                                <div class="col-md-12 mt-4">
                                                    <hr class="border-secondary mb-4">
                                                    <button type="submit" class="btn btn-primary btn-lg w-100"><i class="las la-save"></i> Publish Changes to Live Site</button>
                                                </div>
                                            </div>
                                        </form>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
"""

# Append it right before <!-- TAB: USERS -->
target = '<!-- TAB: USERS -->'
if target in text and "TAB: CUSTOMIZER" not in text:
    text = text.replace(target, customizer_html + '\n                    ' + target)
    with open("app/templates/admin_dashboard.html", "w", encoding="utf-8") as f:
        f.write(text)
    print("Injected tab-customizer")
else:
    print("tab-customizer already exists or target not found")

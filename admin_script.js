
        // Initialize Lucide icons
        lucide.createIcons();

        // Tab Switching Logic
        function switchTab(tabId, elem) {
            // Hide all tabs
            document.querySelectorAll('.admin-tab').forEach(tab => {
                tab.style.display = 'none';
                tab.classList.remove('active');
            });
            
            // Show target tab
            const target = document.getElementById(`tab-${tabId}`);
            if (target) {
                target.style.display = 'block';
                target.classList.add('active');
            }

            // Update sidebar active state
            if (elem) {
                document.querySelectorAll('.sidebar-link').forEach(link => {
                    link.classList.remove('bg-slate-800/50', 'border-slate-700/50', 'text-white', 'active-nav', 'shadow-sm');
                    link.classList.add('text-slate-400', 'border-transparent');
                    // Reset icon color
                    const icon = link.querySelector('i');
                    if(icon && link !== elem) {
                        icon.classList.remove('text-blue-400');
                    }
                });
                
                elem.classList.remove('text-slate-400', 'border-transparent');
                elem.classList.add('bg-slate-800/50', 'border-slate-700/50', 'text-white', 'active-nav', 'shadow-sm');
                
                // Highlight icon
                const activeIcon = elem.querySelector('i');
                if(activeIcon) {
                    activeIcon.classList.add('text-blue-400');
                }
                
                // Update Title if exists in tab
                const pageTitle = document.getElementById('page-title');
                if(pageTitle && tabId === 'dashboard') {
                    pageTitle.innerText = 'Dashboard Overview';
                }
            }
        }

        // Generic API Action Function
        async function adminAction(type, id, action) {
            if(!confirm(`Are you sure you want to perform '${action}' on ${type} #${id}?`)) return;
            
            try {
                const res = await fetch(`/admin/api/${type}/${id}/${action}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                if (res.ok) {
                    showToast(`${type} action '${action}' successful!`);
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showToast(`Failed: ${res.statusText}`);
                }
            } catch (err) {
                console.error(err);
                showToast(`Error: ${err.message}`);
            }
        }

        // Broadcast Form
        async function handleBroadcast(e) {
            e.preventDefault();
            const title = document.getElementById('broadcast_title').value;
            const message = document.getElementById('broadcast_message').value;
            try {
                const res = await fetch('/admin/api/broadcast', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({title, message})
                });
                if (res.ok) {
                    showToast('Broadcast sent successfully!');
                    e.target.reset();
                } else {
                    showToast('Failed to send broadcast');
                }
            } catch (err) {
                showToast('Error sending broadcast');
            }
        }

        // Settings Form
        async function handleSettingsUpdate(e) {
            e.preventDefault();
            const admin_username = document.getElementById('admin_username').value;
            const admin_password = document.getElementById('admin_password').value;
            try {
                const res = await fetch('/admin/api/settings', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({admin_username, admin_password})
                });
                if (res.ok) {
                    showToast('Settings updated successfully!');
                    document.getElementById('admin_password').value = '';
                } else {
                    showToast('Failed to update settings');
                }
            } catch(err) {
                showToast('Error updating settings');
            }
        }

        // Customizer Form
        async function handleCustomizerSubmit(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());
            try {
                const res = await fetch('/admin/api/customize', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                if (res.ok) {
                    showToast('Live site customized successfully!');
                } else {
                    showToast('Update failed');
                }
            } catch(err) {
                showToast('Error updating customizer');
            }
        }

        // Modal Controls
        function openEditUserModal(id, name, email) {
            document.getElementById('edit_user_id').value = id;
            document.getElementById('edit_user_name').value = name;
            document.getElementById('edit_user_email').value = email;
            const modal = document.getElementById('editUserModal');
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }

        function openEditPriceModal(id, price) {
            document.getElementById('edit_pkg_id').value = id;
            document.getElementById('edit_pkg_price').value = price;
            const modal = document.getElementById('editPriceModal');
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }

        function closeModal(modalId) {
            const modal = document.getElementById(modalId);
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }

        async function submitEditUser(e) {
            e.preventDefault();
            const id = document.getElementById('edit_user_id').value;
            const full_name = document.getElementById('edit_user_name').value;
            const email = document.getElementById('edit_user_email').value;
            const password = document.getElementById('edit_user_password').value;

            try {
                const res = await fetch(`/admin/api/user/update`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({id, full_name, email, password})
                });
                if (res.ok) {
                    showToast('User updated successfully!');
                    closeModal('editUserModal');
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showToast('Failed to update user');
                }
            } catch(err) {
                showToast('Error updating user');
            }
        }

        async function submitEditPrice(e) {
            e.preventDefault();
            const id = document.getElementById('edit_pkg_id').value;
            const price = document.getElementById('edit_pkg_price').value;
            try {
                const res = await fetch(`/admin/api/package/${id}/update_price`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({price: parseFloat(price)})
                });
                if (res.ok) {
                    showToast('Price updated!');
                    closeModal('editPriceModal');
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showToast('Failed to update price');
                }
            } catch(err) {
                showToast('Error updating price');
            }
        }

        // Sync color picker inputs
        const colorPicker = document.querySelector('input[type="color"]');
        const colorText = document.querySelector('input[name="primary_color_text"]');
        const colorPreview = document.querySelector('.color-preview');
        
        if(colorPicker && colorText) {
            colorPicker.addEventListener('input', (e) => {
                colorText.value = e.target.value;
                if(colorPreview) colorPreview.style.backgroundColor = e.target.value;
            });
            colorText.addEventListener('input', (e) => {
                colorPicker.value = e.target.value;
                if(colorPreview) colorPreview.style.backgroundColor = e.target.value;
            });
        }

        // Toast Notification
        function showToast(message) {
            const toast = document.getElementById('toast');
            document.getElementById('toastMessage').innerText = message;
            toast.style.transform = 'translateY(0)';
            toast.style.opacity = '1';
            setTimeout(() => {
                toast.style.transform = 'translateY(150%)';
                toast.style.opacity = '0';
            }, 4000);
        }
    
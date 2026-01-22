/**
 * Quick Fill - Save your info for faster form filling
 * Stores user data in localStorage for easy copy/paste to testimony forms
 */

(function() {
  'use strict';

  const STORAGE_KEY = 'wa_bill_tracker_user_info';

  // Default empty user info
  const defaultUserInfo = {
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    zip: '',
    district: ''
  };

  // Load saved user info
  function loadUserInfo() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : { ...defaultUserInfo };
    } catch (e) {
      console.error('Error loading user info:', e);
      return { ...defaultUserInfo };
    }
  }

  // Save user info
  function saveUserInfo(info) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(info));
      return true;
    } catch (e) {
      console.error('Error saving user info:', e);
      return false;
    }
  }

  // Clear user info
  function clearUserInfo() {
    try {
      localStorage.removeItem(STORAGE_KEY);
      return true;
    } catch (e) {
      console.error('Error clearing user info:', e);
      return false;
    }
  }

  // Copy text to clipboard
  function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(() => {
      const originalText = button.textContent;
      button.textContent = 'Copied!';
      button.classList.add('copied');
      setTimeout(() => {
        button.textContent = originalText;
        button.classList.remove('copied');
      }, 1500);
    }).catch(err => {
      console.error('Failed to copy:', err);
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      button.textContent = 'Copied!';
      setTimeout(() => {
        button.textContent = 'Copy';
      }, 1500);
    });
  }

  // Initialize Quick Fill panel
  function initQuickFill() {
    const panel = document.getElementById('quick-fill-panel');
    if (!panel) return;

    const userInfo = loadUserInfo();

    // Populate form fields
    Object.keys(userInfo).forEach(key => {
      const input = panel.querySelector(`[name="${key}"]`);
      if (input) {
        input.value = userInfo[key];
      }
    });

    // Update preview
    updatePreview(userInfo);

    // Save button handler
    const saveBtn = panel.querySelector('.quick-fill-save');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => {
        const newInfo = {};
        Object.keys(defaultUserInfo).forEach(key => {
          const input = panel.querySelector(`[name="${key}"]`);
          if (input) {
            newInfo[key] = input.value.trim();
          }
        });

        if (saveUserInfo(newInfo)) {
          updatePreview(newInfo);
          showNotification('Your information has been saved!', 'success');
        } else {
          showNotification('Failed to save. Please try again.', 'error');
        }
      });
    }

    // Clear button handler
    const clearBtn = panel.querySelector('.quick-fill-clear');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        if (confirm('Clear all saved information?')) {
          clearUserInfo();
          Object.keys(defaultUserInfo).forEach(key => {
            const input = panel.querySelector(`[name="${key}"]`);
            if (input) {
              input.value = '';
            }
          });
          updatePreview(defaultUserInfo);
          showNotification('Information cleared.', 'info');
        }
      });
    }

    // Copy buttons
    panel.querySelectorAll('.copy-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const field = btn.dataset.field;
        const info = loadUserInfo();
        let textToCopy = '';

        if (field === 'full-name') {
          textToCopy = `${info.firstName} ${info.lastName}`.trim();
        } else if (field === 'full-address') {
          textToCopy = [info.address, info.city, 'WA', info.zip].filter(Boolean).join(', ');
        } else if (field === 'all') {
          textToCopy = formatAllInfo(info);
        } else if (info[field]) {
          textToCopy = info[field];
        }

        if (textToCopy) {
          copyToClipboard(textToCopy, btn);
        }
      });
    });

    // Toggle panel visibility
    const toggleBtn = document.querySelector('.quick-fill-toggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        panel.classList.toggle('collapsed');
        const isCollapsed = panel.classList.contains('collapsed');
        toggleBtn.setAttribute('aria-expanded', !isCollapsed);
        localStorage.setItem('quick_fill_collapsed', isCollapsed);
      });

      // Restore collapsed state
      if (localStorage.getItem('quick_fill_collapsed') === 'true') {
        panel.classList.add('collapsed');
        toggleBtn.setAttribute('aria-expanded', 'false');
      }
    }
  }

  // Update the preview section
  function updatePreview(info) {
    const preview = document.querySelector('.quick-fill-preview');
    if (!preview) return;

    const hasData = Object.values(info).some(v => v);

    if (!hasData) {
      preview.innerHTML = '<p class="no-data">No information saved yet. Fill out the form above and click Save.</p>';
      return;
    }

    preview.innerHTML = `
      <div class="preview-row">
        <span class="preview-label">Name:</span>
        <span class="preview-value">${info.firstName} ${info.lastName}</span>
        <button class="copy-btn btn-tiny" data-field="full-name">Copy</button>
      </div>
      ${info.email ? `
      <div class="preview-row">
        <span class="preview-label">Email:</span>
        <span class="preview-value">${info.email}</span>
        <button class="copy-btn btn-tiny" data-field="email">Copy</button>
      </div>
      ` : ''}
      ${info.phone ? `
      <div class="preview-row">
        <span class="preview-label">Phone:</span>
        <span class="preview-value">${info.phone}</span>
        <button class="copy-btn btn-tiny" data-field="phone">Copy</button>
      </div>
      ` : ''}
      ${info.address ? `
      <div class="preview-row">
        <span class="preview-label">Address:</span>
        <span class="preview-value">${info.address}, ${info.city}, WA ${info.zip}</span>
        <button class="copy-btn btn-tiny" data-field="full-address">Copy</button>
      </div>
      ` : ''}
      ${info.district ? `
      <div class="preview-row">
        <span class="preview-label">District:</span>
        <span class="preview-value">${info.district}</span>
        <button class="copy-btn btn-tiny" data-field="district">Copy</button>
      </div>
      ` : ''}
      <div class="preview-row preview-row-all">
        <button class="copy-btn btn-small btn-primary" data-field="all">Copy All Info</button>
      </div>
    `;

    // Re-attach copy button listeners
    preview.querySelectorAll('.copy-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const field = btn.dataset.field;
        let textToCopy = '';

        if (field === 'full-name') {
          textToCopy = `${info.firstName} ${info.lastName}`.trim();
        } else if (field === 'full-address') {
          textToCopy = [info.address, info.city, 'WA', info.zip].filter(Boolean).join(', ');
        } else if (field === 'all') {
          textToCopy = formatAllInfo(info);
        } else if (info[field]) {
          textToCopy = info[field];
        }

        if (textToCopy) {
          copyToClipboard(textToCopy, btn);
        }
      });
    });
  }

  // Format all info for copying
  function formatAllInfo(info) {
    const lines = [];
    if (info.firstName || info.lastName) {
      lines.push(`Name: ${info.firstName} ${info.lastName}`.trim());
    }
    if (info.email) lines.push(`Email: ${info.email}`);
    if (info.phone) lines.push(`Phone: ${info.phone}`);
    if (info.address) {
      lines.push(`Address: ${info.address}, ${info.city}, WA ${info.zip}`);
    }
    if (info.district) lines.push(`Legislative District: ${info.district}`);
    return lines.join('\n');
  }

  // Show notification
  function showNotification(message, type = 'info') {
    const existing = document.querySelector('.quick-fill-notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.className = `quick-fill-notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
      notification.classList.add('show');
    }, 10);

    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }

  // Initialize floating quick copy button on bill pages
  function initQuickCopyButton() {
    const commentLinks = document.querySelectorAll('a[href*="app.leg.wa.gov/pbc/bill"]');
    if (commentLinks.length === 0) return;

    const userInfo = loadUserInfo();
    const hasData = Object.values(userInfo).some(v => v);
    if (!hasData) return;

    // Add a floating indicator
    const indicator = document.createElement('div');
    indicator.className = 'quick-fill-indicator';
    indicator.innerHTML = `
      <span class="indicator-icon">📋</span>
      <span class="indicator-text">Info saved</span>
    `;
    indicator.title = 'Your contact info is saved. Click any Comment button to use it.';
    document.body.appendChild(indicator);
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initQuickFill();
      initQuickCopyButton();
    });
  } else {
    initQuickFill();
    initQuickCopyButton();
  }

  // Expose for external use
  window.QuickFill = {
    load: loadUserInfo,
    save: saveUserInfo,
    clear: clearUserInfo,
    copy: copyToClipboard
  };
})();

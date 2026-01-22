/**
 * Quick Fill - Save your info for faster form filling
 * Stores user data in localStorage for easy copy/paste to testimony forms
 * Enhanced with comment templates for quick bill responses
 */

(function() {
  'use strict';

  const STORAGE_KEY = 'wa_bill_tracker_user_info';
  const TEMPLATES_KEY = 'wa_bill_tracker_comment_templates';

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

  // Default comment templates
  const defaultTemplates = {
    support: "I am writing in SUPPORT of this bill. As a Washington resident, I believe this legislation will benefit our community by [YOUR REASON]. I urge you to vote YES on this bill.",
    oppose: "I am writing in OPPOSITION to this bill. As a Washington resident, I am concerned that this legislation would [YOUR CONCERN]. I urge you to vote NO on this bill.",
    neutral: "I am writing regarding this bill. As a Washington resident, I would like to share my perspective: [YOUR COMMENTS]."
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

  // Load comment templates
  function loadTemplates() {
    try {
      const saved = localStorage.getItem(TEMPLATES_KEY);
      return saved ? { ...defaultTemplates, ...JSON.parse(saved) } : { ...defaultTemplates };
    } catch (e) {
      console.error('Error loading templates:', e);
      return { ...defaultTemplates };
    }
  }

  // Save comment templates
  function saveTemplates(templates) {
    try {
      localStorage.setItem(TEMPLATES_KEY, JSON.stringify(templates));
      return true;
    } catch (e) {
      console.error('Error saving templates:', e);
      return false;
    }
  }

  // Generate a complete comment for a bill
  function generateComment(billNumber, position, customReason, userInfo) {
    const templates = loadTemplates();
    const info = userInfo || loadUserInfo();

    let template = templates[position] || templates.neutral;

    // Replace placeholder with custom reason if provided
    if (customReason && customReason.trim()) {
      template = template
        .replace('[YOUR REASON]', customReason.trim())
        .replace('[YOUR CONCERN]', customReason.trim())
        .replace('[YOUR COMMENTS]', customReason.trim());
    }

    // Build the full comment
    const lines = [];

    // Add greeting with bill number
    lines.push(`RE: ${billNumber}`);
    lines.push('');
    lines.push(template);
    lines.push('');

    // Add signature block
    lines.push('Sincerely,');
    if (info.firstName || info.lastName) {
      lines.push(`${info.firstName} ${info.lastName}`.trim());
    }
    if (info.address) {
      lines.push(`${info.address}`);
      lines.push(`${info.city}, WA ${info.zip}`);
    }
    if (info.district) {
      lines.push(`Legislative District ${info.district}`);
    }
    if (info.email) {
      lines.push(info.email);
    }
    if (info.phone) {
      lines.push(info.phone);
    }

    return lines.join('\n');
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

  // Initialize the bill page comment helper
  function initBillPageHelper() {
    const billPage = document.querySelector('.bill-page');
    if (!billPage) return;

    // Get bill number from the page
    const billNumberEl = billPage.querySelector('.bill-number');
    if (!billNumberEl) return;

    const billNumber = billNumberEl.textContent.trim();
    const userInfo = loadUserInfo();
    const hasUserInfo = Object.values(userInfo).some(v => v);

    // Find the actions panel and insert our helper after it
    const actionsPanel = billPage.querySelector('.actions-panel');
    if (!actionsPanel) return;

    // Create the Quick Comment panel
    const panel = document.createElement('section');
    panel.className = 'quick-comment-panel';
    panel.innerHTML = `
      <h2>Quick Comment Builder</h2>
      <p class="panel-subtitle">Build your comment in seconds, then copy and paste into the official form.</p>

      ${!hasUserInfo ? `
      <div class="quick-comment-notice">
        <p><strong>Save time!</strong> <a href="/how-to-act/#quick-fill">Save your contact info</a> once, use it on every bill.</p>
      </div>
      ` : ''}

      <div class="position-selector">
        <label class="position-label">Your Position:</label>
        <div class="position-buttons">
          <button type="button" class="position-btn position-support" data-position="support">
            <span class="position-icon">👍</span>
            <span class="position-text">Support</span>
          </button>
          <button type="button" class="position-btn position-oppose" data-position="oppose">
            <span class="position-icon">👎</span>
            <span class="position-text">Oppose</span>
          </button>
          <button type="button" class="position-btn position-neutral" data-position="neutral">
            <span class="position-icon">💬</span>
            <span class="position-text">Comment</span>
          </button>
        </div>
      </div>

      <div class="reason-input" style="display: none;">
        <label for="custom-reason">Add your reason (optional):</label>
        <textarea id="custom-reason" placeholder="Why do you support/oppose this bill? Personal stories are powerful!" rows="3"></textarea>
        <p class="reason-hint">Tip: Personal stories about how this bill affects you are most impactful.</p>
      </div>

      <div class="comment-preview" style="display: none;">
        <label>Your Comment Preview:</label>
        <div class="preview-box">
          <pre class="preview-text"></pre>
        </div>
        <div class="preview-actions">
          <button type="button" class="btn btn-primary btn-large copy-comment-btn">
            <span class="btn-icon">📋</span> Copy Full Comment
          </button>
          <button type="button" class="btn btn-secondary edit-comment-btn">Edit</button>
        </div>
        <p class="next-step">
          <strong>Next:</strong> Click "Comment on This Bill" above, paste your comment, and submit!
        </p>
      </div>
    `;

    actionsPanel.after(panel);

    // Set up event handlers
    const positionBtns = panel.querySelectorAll('.position-btn');
    const reasonInput = panel.querySelector('.reason-input');
    const commentPreview = panel.querySelector('.comment-preview');
    const previewText = panel.querySelector('.preview-text');
    const customReasonTextarea = panel.querySelector('#custom-reason');
    const copyBtn = panel.querySelector('.copy-comment-btn');
    const editBtn = panel.querySelector('.edit-comment-btn');

    let selectedPosition = null;

    // Position button click handlers
    positionBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        // Update selected state
        positionBtns.forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedPosition = btn.dataset.position;

        // Show reason input
        reasonInput.style.display = 'block';

        // Update placeholder based on position
        if (selectedPosition === 'support') {
          customReasonTextarea.placeholder = 'Why do you support this bill? (e.g., "it will help families like mine by...")';
        } else if (selectedPosition === 'oppose') {
          customReasonTextarea.placeholder = 'Why do you oppose this bill? (e.g., "it would negatively impact my community by...")';
        } else {
          customReasonTextarea.placeholder = 'What would you like to share about this bill?';
        }

        // Generate and show preview
        updatePreview();
      });
    });

    // Update preview when reason changes
    customReasonTextarea.addEventListener('input', debounce(updatePreview, 300));

    function updatePreview() {
      if (!selectedPosition) return;

      const comment = generateComment(
        billNumber,
        selectedPosition,
        customReasonTextarea.value,
        userInfo
      );

      previewText.textContent = comment;
      commentPreview.style.display = 'block';

      // Scroll to preview
      commentPreview.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // Copy button handler
    copyBtn.addEventListener('click', () => {
      const comment = previewText.textContent;
      copyToClipboard(comment, copyBtn);

      // Update button text temporarily
      const originalHTML = copyBtn.innerHTML;
      copyBtn.innerHTML = '<span class="btn-icon">✓</span> Copied!';
      copyBtn.classList.add('copied');

      setTimeout(() => {
        copyBtn.innerHTML = originalHTML;
        copyBtn.classList.remove('copied');
      }, 2000);
    });

    // Edit button handler
    editBtn.addEventListener('click', () => {
      customReasonTextarea.focus();
    });
  }

  // Debounce helper
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initQuickFill();
      initQuickCopyButton();
      initBillPageHelper();
    });
  } else {
    initQuickFill();
    initQuickCopyButton();
    initBillPageHelper();
  }

  // Expose for external use
  window.QuickFill = {
    load: loadUserInfo,
    save: saveUserInfo,
    clear: clearUserInfo,
    copy: copyToClipboard,
    loadTemplates: loadTemplates,
    saveTemplates: saveTemplates,
    generateComment: generateComment
  };
})();

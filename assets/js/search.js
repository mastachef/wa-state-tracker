/**
 * WA Bill Tracker - Search and Filter Functionality
 * Client-side filtering for the bills list
 */

(function() {
  'use strict';

  // Only run on pages with bill filtering
  const searchInput = document.getElementById('bill-search');
  const billsContainer = document.getElementById('bills-container');

  if (!searchInput || !billsContainer) return;

  // DOM elements
  const clearButton = document.getElementById('clear-search');
  const chamberFilter = document.getElementById('filter-chamber');
  const statusFilter = document.getElementById('filter-status');
  const threatFilter = document.getElementById('filter-threat');
  const sortBy = document.getElementById('sort-by');
  const resultsCount = document.getElementById('results-count');
  const noResults = document.getElementById('no-results');
  const resetButton = document.getElementById('reset-filters');

  // Get all bill cards
  let billCards = Array.from(billsContainer.querySelectorAll('.bill-card'));

  /**
   * Filter and display bills based on current criteria
   */
  function filterBills() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const chamber = chamberFilter ? chamberFilter.value.toLowerCase() : '';
    const status = statusFilter ? statusFilter.value.toLowerCase() : '';
    const threat = threatFilter ? threatFilter.value.toLowerCase() : '';

    let visibleCount = 0;

    billCards.forEach(card => {
      const billNumber = card.dataset.billNumber || '';
      const title = card.dataset.title || '';
      const description = card.dataset.description || '';
      const cardChamber = card.dataset.chamber || '';
      const cardStatus = card.dataset.status || '';
      const cardThreat = card.dataset.threat || '';

      // Search matching
      const matchesSearch = !searchTerm ||
        billNumber.includes(searchTerm) ||
        title.includes(searchTerm) ||
        description.includes(searchTerm);

      // Chamber matching
      const matchesChamber = !chamber || cardChamber.includes(chamber);

      // Status matching
      const matchesStatus = !status || cardStatus.includes(status);

      // Threat level matching
      const matchesThreat = !threat || cardThreat === threat;

      // Show/hide card
      if (matchesSearch && matchesChamber && matchesStatus && matchesThreat) {
        card.style.display = '';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    // Update results count
    if (resultsCount) {
      resultsCount.textContent = `${visibleCount} bill${visibleCount !== 1 ? 's' : ''} found`;
    }

    // Show/hide no results message
    if (noResults) {
      noResults.style.display = visibleCount === 0 ? '' : 'none';
    }
    billsContainer.style.display = visibleCount === 0 ? 'none' : '';
  }

  /**
   * Sort bills by selected criteria
   */
  function sortBills() {
    if (!sortBy) return;

    const sortValue = sortBy.value;

    billCards.sort((a, b) => {
      switch (sortValue) {
        case 'number':
          return (a.dataset.billNumber || '').localeCompare(b.dataset.billNumber || '', undefined, { numeric: true });
        case 'title':
          return (a.dataset.title || '').localeCompare(b.dataset.title || '');
        case 'recent':
        default:
          // Sort by date descending (most recent first)
          const dateA = a.dataset.date || '';
          const dateB = b.dataset.date || '';
          return dateB.localeCompare(dateA);
      }
    });

    // Re-append sorted cards
    billCards.forEach(card => billsContainer.appendChild(card));

    // Re-filter after sort
    filterBills();
  }

  /**
   * Reset all filters to default
   */
  function resetFilters() {
    searchInput.value = '';
    if (chamberFilter) chamberFilter.value = '';
    if (statusFilter) statusFilter.value = '';
    if (threatFilter) threatFilter.value = '';
    if (sortBy) sortBy.value = 'recent';

    sortBills();
  }

  /**
   * Debounce function to limit rapid calls
   */
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

  // Event listeners
  const debouncedFilter = debounce(filterBills, 200);

  searchInput.addEventListener('input', debouncedFilter);

  if (clearButton) {
    clearButton.addEventListener('click', () => {
      searchInput.value = '';
      filterBills();
      searchInput.focus();
    });
  }

  if (chamberFilter) {
    chamberFilter.addEventListener('change', filterBills);
  }

  if (statusFilter) {
    statusFilter.addEventListener('change', filterBills);
  }

  if (threatFilter) {
    threatFilter.addEventListener('change', filterBills);
  }

  if (sortBy) {
    sortBy.addEventListener('change', sortBills);
  }

  if (resetButton) {
    resetButton.addEventListener('click', resetFilters);
  }

  // Handle URL parameters for direct linking
  function handleUrlParams() {
    const params = new URLSearchParams(window.location.search);

    if (params.has('search')) {
      searchInput.value = params.get('search');
    }
    if (params.has('chamber') && chamberFilter) {
      chamberFilter.value = params.get('chamber');
    }
    if (params.has('status') && statusFilter) {
      statusFilter.value = params.get('status');
    }
    if (params.has('threat') && threatFilter) {
      threatFilter.value = params.get('threat');
    }

    filterBills();
  }

  // Initialize
  handleUrlParams();

  // Mobile menu toggle
  const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
  const mainNav = document.querySelector('.main-nav');

  if (mobileMenuToggle && mainNav) {
    mobileMenuToggle.addEventListener('click', () => {
      mainNav.classList.toggle('active');
      mobileMenuToggle.classList.toggle('active');
    });
  }
})();

// Mobile navigation styles (add to page dynamically)
(function() {
  const style = document.createElement('style');
  style.textContent = `
    @media (max-width: 768px) {
      .main-nav {
        display: none;
        position: absolute;
        top: 64px;
        left: 0;
        right: 0;
        background: white;
        border-bottom: 1px solid var(--color-slate-200);
        padding: var(--space-4);
        box-shadow: var(--shadow-md);
      }

      .main-nav.active {
        display: block;
      }

      .main-nav ul {
        flex-direction: column;
        gap: 0;
      }

      .main-nav li {
        border-bottom: 1px solid var(--color-slate-100);
      }

      .main-nav li:last-child {
        border-bottom: none;
      }

      .main-nav a {
        display: block;
        padding: var(--space-3) 0;
      }

      .mobile-menu-toggle.active span:nth-child(1) {
        transform: rotate(45deg) translate(5px, 5px);
      }

      .mobile-menu-toggle.active span:nth-child(2) {
        opacity: 0;
      }

      .mobile-menu-toggle.active span:nth-child(3) {
        transform: rotate(-45deg) translate(5px, -5px);
      }
    }
  `;
  document.head.appendChild(style);
})();

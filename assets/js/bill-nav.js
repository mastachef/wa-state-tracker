/**
 * Bill page navigation - adds prev/next arrows on sides
 */
(function() {
  // Only run on bill pages
  const billPage = document.querySelector('.bill-page');
  if (!billPage) return;

  // Get current bill number from the page
  const billNumberEl = document.querySelector('.bill-number');
  if (!billNumberEl) return;
  const currentBillNumber = billNumberEl.textContent.trim();

  // Detect base path from current URL (for GitHub Pages vs custom domain)
  const basePath = window.location.pathname.startsWith('/wa-state-tracker') ? '/wa-state-tracker' : '';

  // Fetch bills data
  fetch(basePath + '/api/bills.json')
    .then(response => {
      if (!response.ok) throw new Error('Not found');
      return response.json();
    })
    .then(bills => setupNavigation(bills, currentBillNumber, basePath))
    .catch(err => console.log('Bill navigation: Could not load bills data', err));

  function setupNavigation(bills, currentBillNumber, basePath) {
    // Find current bill index
    const currentIndex = bills.findIndex(b => b.bill_number === currentBillNumber);
    if (currentIndex === -1) return;

    const prevBill = currentIndex > 0 ? bills[currentIndex - 1] : null;
    const nextBill = currentIndex < bills.length - 1 ? bills[currentIndex + 1] : null;

    // Create navigation container
    const nav = document.createElement('nav');
    nav.className = 'side-nav';
    nav.setAttribute('aria-label', 'Bill navigation');

    // Previous arrow
    if (prevBill) {
      const prevLink = document.createElement('a');
      prevLink.href = basePath + '/bill/' + slugify(prevBill.bill_number) + '/';
      prevLink.className = 'side-nav-arrow side-nav-prev';
      prevLink.setAttribute('aria-label', 'Previous bill: ' + prevBill.bill_number);
      prevLink.innerHTML = `
        <span class="arrow-icon">&larr;</span>
        <span class="arrow-label">
          <span class="arrow-direction">Previous</span>
          <span class="arrow-bill">${prevBill.bill_number}</span>
        </span>
      `;
      nav.appendChild(prevLink);
    }

    // Next arrow
    if (nextBill) {
      const nextLink = document.createElement('a');
      nextLink.href = basePath + '/bill/' + slugify(nextBill.bill_number) + '/';
      nextLink.className = 'side-nav-arrow side-nav-next';
      nextLink.setAttribute('aria-label', 'Next bill: ' + nextBill.bill_number);
      nextLink.innerHTML = `
        <span class="arrow-label">
          <span class="arrow-direction">Next</span>
          <span class="arrow-bill">${nextBill.bill_number}</span>
        </span>
        <span class="arrow-icon">&rarr;</span>
      `;
      nav.appendChild(nextLink);
    }

    document.body.appendChild(nav);

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
      // Don't navigate if user is typing in an input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      if (e.key === 'ArrowLeft' && prevBill) {
        window.location.href = basePath + '/bill/' + slugify(prevBill.bill_number) + '/';
      } else if (e.key === 'ArrowRight' && nextBill) {
        window.location.href = basePath + '/bill/' + slugify(nextBill.bill_number) + '/';
      }
    });
  }

  function slugify(text) {
    return text.toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/[-\s]+/g, '-')
      .trim();
  }
})();

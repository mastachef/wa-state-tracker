/**
 * WA Bill Tracker - Mobile Menu
 * Hamburger menu toggle for mobile navigation
 */

(function() {
  'use strict';

  const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
  const mainNav = document.querySelector('.main-nav');

  if (mobileMenuToggle && mainNav) {
    mobileMenuToggle.addEventListener('click', function(e) {
      e.preventDefault();
      mainNav.classList.toggle('active');
      mobileMenuToggle.classList.toggle('active');
    });

    document.addEventListener('click', function(e) {
      if (!mainNav.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
        mainNav.classList.remove('active');
        mobileMenuToggle.classList.remove('active');
      }
    });
  }
})();

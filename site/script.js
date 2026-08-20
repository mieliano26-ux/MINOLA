// תפריט מובייל
const toggle = document.getElementById('navToggle');
const nav = document.getElementById('nav');

if (toggle && nav) {
  toggle.addEventListener('click', () => nav.classList.toggle('open'));
  // סגירת התפריט אחרי לחיצה על קישור
  nav.querySelectorAll('a').forEach((link) =>
    link.addEventListener('click', () => nav.classList.remove('open'))
  );
}

// שנה נוכחית בפוטר
const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

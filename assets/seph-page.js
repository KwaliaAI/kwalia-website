// One shared CTA value serves both languages. A channel href replaces the signup.
(async function(){
  try {
    const response = await fetch('/data/seph-cta.json');
    if (!response.ok) return;
    const cta = await response.json(), lang = document.documentElement.lang;
    if (!cta.label || typeof cta.label[lang] !== 'string') return;
    if (cta.href) {
      const target = new URL(cta.href);
      if (target.protocol !== 'https:') return;
      const link = document.getElementById('seph-channel');
      link.href = target.href; link.textContent = cta.label[lang]; link.hidden = false;
      document.getElementById('seph-signup').hidden = true;
    } else document.querySelector('#seph-signup button').textContent = cta.label[lang];
  } catch {} // The approved signup remains usable if config cannot be fetched.
})();
function ml_webform_success_27105567(){
  document.querySelector('#seph-signup .row-form').hidden = true;
  const success = document.querySelector('#seph-signup .row-success');
  success.hidden = false;
  success.setAttribute('tabindex','-1'); success.focus();
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({event:'newsletter_signup',form_location:'seph_page'});
}

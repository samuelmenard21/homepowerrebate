/**
 * HomePowerRebate Form Submission Handlers
 * Wires all forms to POST to https://leads.homepowerrebate.com/[endpoint]
 *
 * Includes:
 * - Email breakdown form (#hpr-email-form) → /newsletter
 * - Installer match form (#hpr-refer-form) → /estimate-lead
 * - Waitlist form (#waitlist-form) → /waitlist
 * - Newsletter form (#newsletter-form) → /newsletter
 */

const WORKER_URL = 'https://leads.homepowerrebate.com';

/**
 * Serialize form data to JSON and POST to Worker
 */
async function submitForm(formElement, endpoint) {
  const formData = new FormData(formElement);
  const data = Object.fromEntries(formData);

  try {
    const response = await fetch(`${WORKER_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    if (response.ok && result.success) {
      return { success: true, data: result };
    } else {
      return { success: false, error: result.error || 'Unknown error' };
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Show success/error message to user
 */
function showMessage(element, message, isSuccess) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `form-message ${isSuccess ? 'success' : 'error'}`;
  messageDiv.textContent = message;
  messageDiv.style.cssText = `
    padding: 12px 16px;
    margin: 12px 0;
    border-radius: 8px;
    background: ${isSuccess ? '#d4e5d8' : '#f5d9d9'};
    color: ${isSuccess ? '#2d6a4f' : '#8b3a3a'};
    font-size: 14px;
  `;
  element.parentNode.insertBefore(messageDiv, element.nextSibling);
}

// ============================================================================
// FORM 1: Email Breakdown Form (#hpr-email-form)
// Endpoint: /newsletter
// Fields: email, firstname (name), newsletter checkbox
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  const emailForm = document.getElementById('hpr-email-form');
  if (emailForm) {
    // Add name attribute to unnamed fields
    const emailInput = emailForm.querySelector('input[type="email"]');
    if (emailInput && !emailInput.name) emailInput.name = 'email';

    const nameInput = emailForm.querySelector('input[type="text"]');
    if (nameInput && !nameInput.name) nameInput.name = 'firstname';

    const newsletterCheckbox = emailForm.querySelector('input[type="checkbox"]');
    if (newsletterCheckbox && !newsletterCheckbox.name) newsletterCheckbox.name = 'newsletter';

    emailForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const submitBtn = emailForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Sending...';

      const result = await submitForm(emailForm, '/newsletter');

      if (result.success) {
        showMessage(emailForm, '✓ Got it! Check your email for your breakdown.', true);
        emailForm.reset();
      } else {
        showMessage(emailForm, `✗ Error: ${result.error}`, false);
      }

      submitBtn.disabled = false;
      submitBtn.textContent = emailForm.dataset.originalText || 'Email my breakdown →';
    });
  }
});

// ============================================================================
// FORM 2: Installer Match Form (#hpr-refer-form)
// Endpoint: /estimate-lead
// Fields: firstname, phone, [email, city from page context]
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  const matchForm = document.getElementById('hpr-refer-form');
  if (matchForm) {
    // Add name attributes
    const firstNameInput = matchForm.querySelector('input[placeholder="First name"]');
    if (firstNameInput && !firstNameInput.name) firstNameInput.name = 'firstname';

    const phoneInput = matchForm.querySelector('input[type="tel"]');
    if (phoneInput && !phoneInput.name) phoneInput.name = 'phone';

    matchForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Collect form data
      const formData = new FormData(matchForm);
      const data = Object.fromEntries(formData);

      // Add current page context
      data.page_url = window.location.href;
      data.source = window.location.pathname;

      // Try to detect city from URL
      const cityMatch = window.location.pathname.match(/\/ca\/bc\/([a-z-]+)/);
      if (cityMatch) {
        data.city = cityMatch[1].replace('-', ' ');
      }

      // Prompt for email if not already provided
      if (!data.email) {
        data.email = prompt('Please enter your email address:');
        if (!data.email) return;
      }

      // Validate email
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
        showMessage(matchForm, '✗ Please enter a valid email address.', false);
        return;
      }

      const submitBtn = matchForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Finding installer...';

      try {
        const response = await fetch(`${WORKER_URL}/estimate-lead`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok && result.success) {
          showMessage(matchForm, `✓ Done! ${result.installer_name ? result.installer_name + ' will' : 'An installer will'} be in touch.`, true);
          matchForm.reset();
        } else {
          showMessage(matchForm, `✗ Error: ${result.error || 'Could not submit'}`, false);
        }
      } catch (error) {
        showMessage(matchForm, `✗ Connection error: ${error.message}`, false);
      }

      submitBtn.disabled = false;
      submitBtn.textContent = 'Match me with my installer →';
    });
  }
});

// ============================================================================
// FORM 3: Waitlist Form (#waitlist-form)
// Endpoint: /waitlist
// Fields: email, city_name (for area), postal
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  const waitlistForm = document.getElementById('waitlist-form');
  if (waitlistForm) {
    waitlistForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const submitBtn = waitlistForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Adding to waitlist...';

      const result = await submitForm(waitlistForm, '/waitlist');

      if (result.success) {
        showMessage(waitlistForm, "✓ You're on the list! We'll email you when we're live in your area.", true);
        waitlistForm.reset();
      } else {
        showMessage(waitlistForm, `✗ Error: ${result.error}`, false);
      }

      submitBtn.disabled = false;
      submitBtn.textContent = 'Join the waitlist →';
    });
  }
});

// ============================================================================
// FORM 4: Newsletter Form (#newsletter-form)
// Endpoint: /newsletter
// Fields: email, city (select dropdown)
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  const newsletterForm = document.getElementById('newsletter-form');
  if (newsletterForm) {
    // Add name attributes
    const emailInput = newsletterForm.querySelector('input[type="email"]');
    if (emailInput && !emailInput.name) emailInput.name = 'email';

    const citySelect = newsletterForm.querySelector('select');
    if (citySelect && !citySelect.name) citySelect.name = 'city';

    newsletterForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const submitBtn = newsletterForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Subscribing...';

      const result = await submitForm(newsletterForm, '/newsletter');

      if (result.success) {
        showMessage(newsletterForm, '✓ Check your inbox for weekly BC rebate insights!', true);
        newsletterForm.reset();
      } else {
        showMessage(newsletterForm, `✗ Error: ${result.error}`, false);
      }

      submitBtn.disabled = false;
      submitBtn.textContent = 'Send me weekly insights';
    });
  }
});

console.log('HomePowerRebate form handlers loaded');

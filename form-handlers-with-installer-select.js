/**
 * HomePowerRebate Form Submission Handlers (with Installer Selection)
 *
 * Includes installer chooser for city page forms + calculator
 * Profile pages submit directly to that installer
 */

const WORKER_URL = 'https://leads.homepowerrebate.com';
const INSTALLERS_JSON_BASE = '/installers/json';

/**
 * Load installers for a city from JSON
 */
async function loadInstallersForCity(city) {
  try {
    const response = await fetch(`${INSTALLERS_JSON_BASE}/${city.toLowerCase().replace(' ', '-')}.json`);
    if (response.ok) {
      return await response.json();
    }
  } catch (e) {
    console.error(`Failed to load installers for ${city}:`, e);
  }
  return [];
}

/**
 * Show installer chooser modal
 */
function showInstallerChooser(installers, onSelect, onCancel) {
  const modal = document.createElement('div');
  modal.className = 'hpr-modal-overlay';
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
  `;

  const modalContent = document.createElement('div');
  modalContent.className = 'hpr-modal-content';
  modalContent.style.cssText = `
    background: white;
    border-radius: 12px;
    padding: 32px;
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  `;

  const title = document.createElement('h2');
  title.textContent = 'Choose Your Installer';
  title.style.cssText = 'margin: 0 0 16px 0; font-size: 24px; color: #08363f;';
  modalContent.appendChild(title);

  const subtitle = document.createElement('p');
  subtitle.textContent = 'Select which installer you\'d like to get a quote from:';
  subtitle.style.cssText = 'color: #1a3d42; margin-bottom: 20px; font-size: 14px;';
  modalContent.appendChild(subtitle);

  const list = document.createElement('div');
  list.style.cssText = 'margin-bottom: 20px;';

  installers.forEach((installer) => {
    const item = document.createElement('button');
    item.type = 'button';
    item.style.cssText = `
      display: block;
      width: 100%;
      padding: 16px;
      margin-bottom: 8px;
      border: 2px solid #d9d0c1;
      border-radius: 8px;
      background: white;
      cursor: pointer;
      text-align: left;
      transition: all 0.2s;
    `;
    item.onmouseover = () => item.style.borderColor = '#d4751c';
    item.onmouseout = () => item.style.borderColor = '#d9d0c1';

    const name = document.createElement('div');
    name.style.cssText = 'font-weight: 600; color: #08363f; margin-bottom: 4px;';
    name.textContent = installer.name;

    const details = document.createElement('div');
    details.style.cssText = 'font-size: 13px; color: #1a3d42;';
    details.textContent = `${installer.specialty} • ${installer.rating}★ (${installer.reviews} reviews)`;

    const contact = document.createElement('div');
    contact.style.cssText = 'font-size: 12px; color: #6b7d80; margin-top: 4px;';
    contact.textContent = installer.phone;

    item.appendChild(name);
    item.appendChild(details);
    item.appendChild(contact);

    item.onclick = () => {
      modal.remove();
      onSelect(installer);
    };

    list.appendChild(item);
  });

  modalContent.appendChild(list);

  const buttonContainer = document.createElement('div');
  buttonContainer.style.cssText = 'display: flex; gap: 12px;';

  const cancelBtn = document.createElement('button');
  cancelBtn.type = 'button';
  cancelBtn.textContent = 'Cancel';
  cancelBtn.style.cssText = `
    flex: 1;
    padding: 12px;
    border: 1px solid #d9d0c1;
    background: white;
    border-radius: 8px;
    cursor: pointer;
    color: #08363f;
    font-weight: 600;
  `;
  cancelBtn.onclick = () => {
    modal.remove();
    onCancel();
  };

  buttonContainer.appendChild(cancelBtn);
  modalContent.appendChild(buttonContainer);
  modal.appendChild(modalContent);
  document.body.appendChild(modal);
}

/**
 * Submit form with selected installer
 */
async function submitFormWithInstaller(formElement, endpoint, selectedInstaller) {
  const formData = new FormData(formElement);
  const data = Object.fromEntries(formData);

  // Add installer info
  data.installer_name = selectedInstaller.name;
  data.installer_email = selectedInstaller.email || '';
  data.installer_phone = selectedInstaller.phone || '';

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
 * Show message to user
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
// Initialize all forms on page load
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {

  // ========== FORM: Installer Match (with chooser) =========
  // Works on both homepage (#hpr-refer-form) and city pages (#hpr-cw-refer-form)
  const matchForm = document.getElementById('hpr-refer-form') || document.getElementById('hpr-cw-refer-form');
  if (matchForm) {
    // Add name attributes
    const firstNameInput = matchForm.querySelector('input[placeholder="First name"]');
    if (firstNameInput && !firstNameInput.name) firstNameInput.name = 'firstname';

    const phoneInput = matchForm.querySelector('input[type="tel"]');
    if (phoneInput && !phoneInput.name) phoneInput.name = 'phone';

    matchForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Get city from URL
      const cityMatch = window.location.pathname.match(/\/ca\/bc\/([a-z-]+)/);
      if (!cityMatch) {
        showMessage(matchForm, '✗ Could not detect your city. Please try again.', false);
        return;
      }

      const citySlug = cityMatch[1];
      const cityName = citySlug.replace('-', ' ');

      const submitBtn = matchForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Loading installers...';

      // Load installers
      const installers = await loadInstallersForCity(cityName);

      if (!installers || installers.length === 0) {
        showMessage(matchForm, '✗ No installers found for your city.', false);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Match me with my installer →';
        return;
      }

      // Show installer chooser
      showInstallerChooser(
        installers,
        async (selectedInstaller) => {
          // Collect form data
          const formData = new FormData(matchForm);
          const data = Object.fromEntries(formData);

          // Add installer and page context
          data.installer_name = selectedInstaller.name;
          data.installer_email = selectedInstaller.email || '';
          data.installer_phone = selectedInstaller.phone || '';
          data.city = cityName;
          data.page_url = window.location.href;

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

          submitBtn.disabled = true;
          submitBtn.textContent = `Sending to ${selectedInstaller.name.split(' ')[0]}...`;

          try {
            const response = await fetch(`${WORKER_URL}/estimate-lead`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok && result.success) {
              showMessage(matchForm, `✓ Perfect! ${selectedInstaller.name} will contact you soon.`, true);
              matchForm.reset();
            } else {
              showMessage(matchForm, `✗ Error: ${result.error || 'Could not submit'}`, false);
            }
          } catch (error) {
            showMessage(matchForm, `✗ Connection error: ${error.message}`, false);
          }

          submitBtn.disabled = false;
          submitBtn.textContent = 'Match me with my installer →';
        },
        () => {
          // Cancel
          submitBtn.disabled = false;
          submitBtn.textContent = 'Match me with my installer →';
        }
      );
    });
  }

  // ========== FORM: Email Breakdown =========
  const emailForm = document.getElementById('hpr-email-form');
  if (emailForm) {
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

      const formData = new FormData(emailForm);
      const data = Object.fromEntries(formData);

      try {
        const response = await fetch(`${WORKER_URL}/newsletter`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });

        if (response.ok) {
          showMessage(emailForm, '✓ Got it! Check your email for your breakdown.', true);
          emailForm.reset();
        } else {
          const result = await response.json();
          showMessage(emailForm, `✗ Error: ${result.error}`, false);
        }
      } catch (error) {
        showMessage(emailForm, `✗ Connection error: ${error.message}`, false);
      }

      submitBtn.disabled = false;
      submitBtn.textContent = 'Email my breakdown →';
    });
  }

  // ========== FORM: Waitlist =========
  const waitlistForm = document.getElementById('waitlist-form');
  if (waitlistForm) {
    waitlistForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const submitBtn = waitlistForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Adding to waitlist...';

      const formData = new FormData(waitlistForm);
      const data = Object.fromEntries(formData);

      try {
        const response = await fetch(`${WORKER_URL}/waitlist`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });

        if (response.ok) {
          showMessage(waitlistForm, "✓ You're on the list! We'll email you when we're live in your area.", true);
          waitlistForm.reset();
        } else {
          const result = await response.json();
          showMessage(waitlistForm, `✗ Error: ${result.error}`, false);
        }
      } catch (error) {
        showMessage(waitlistForm, `✗ Connection error: ${error.message}`, false);
      }

      submitBtn.disabled = false;
      submitBtn.textContent = 'Join the waitlist';
    });
  }

  // ========== FORM: Newsletter =========
  const newsletterForm = document.getElementById('newsletter-form');
  if (newsletterForm) {
    const emailInput = newsletterForm.querySelector('input[type="email"]');
    if (emailInput && !emailInput.name) emailInput.name = 'email';

    const citySelect = newsletterForm.querySelector('select');
    if (citySelect && !citySelect.name) citySelect.name = 'city';

    newsletterForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const submitBtn = newsletterForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Subscribing...';

      const formData = new FormData(newsletterForm);
      const data = Object.fromEntries(formData);

      try {
        const response = await fetch(`${WORKER_URL}/newsletter`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });

        if (response.ok) {
          showMessage(newsletterForm, '✓ Check your inbox for weekly BC rebate insights!', true);
          newsletterForm.reset();
        } else {
          const result = await response.json();
          showMessage(newsletterForm, `✗ Error: ${result.error}`, false);
        }
      } catch (error) {
        showMessage(newsletterForm, `✗ Connection error: ${error.message}`, false);
      }

      submitBtn.disabled = false;
      submitBtn.textContent = 'Send me weekly insights';
    });
  }

});

console.log('✓ HomePowerRebate form handlers loaded with installer selection');

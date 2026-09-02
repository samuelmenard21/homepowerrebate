/**
 * HomePowerRebate Form Submission Handlers (with Installer Selection)
 *
 * Includes installer chooser for city page forms + calculator
 * Profile pages submit directly to that installer
 */

const WORKER_URL = 'https://leads.homepowerrebate.com';
const INSTALLERS_JSON_BASE = '/installers/json';

// BC's installer JSON lives directly under /installers/json — every other
// region lives under its own subpath (mirrors installers/json/{on,ab,ns,ma}
// on disk, from generate_installer_json_from_real.py's per-region out_dir).
const REGION_PATH_PREFIX = { BC: '', ON: 'on', AB: 'ab', NS: 'ns', MA: 'ma', CA: 'ca', NY: 'ny', PA: 'pa', CO: 'co', VT: 'vt' };

/**
 * Load installers for a city, merging heat-pump + solar directories so a
 * homeowner interested in either trade sees a complete chooser. Region-aware:
 * BC reads the flat path, every other province/state reads its own subpath.
 */
async function loadInstallersForCity(city, province) {
  const prefix = REGION_PATH_PREFIX[(province || 'BC').toUpperCase()] ?? '';
  const base = prefix ? `${INSTALLERS_JSON_BASE}/${prefix}` : INSTALLERS_JSON_BASE;
  const slug = city.toLowerCase().replace(/\s+/g, '-');

  async function safeFetch(url) {
    try {
      const r = await fetch(url);
      return r.ok ? await r.json() : [];
    } catch (e) {
      return [];
    }
  }

  try {
    const [hp, solar] = await Promise.all([
      safeFetch(`${base}/${slug}.json`),
      safeFetch(`${base}/solar/${slug}.json`)
    ]);
    const byName = new Map();
    [...hp, ...solar].forEach(inst => {
      if (inst && inst.name && inst.email) byName.set(inst.name, inst);
    });
    return [...byName.values()];
  } catch (e) {
    console.error(`Failed to load installers for ${city}, ${province}:`, e);
    return [];
  }
}

/**
 * Show installer chooser modal (with multi-select checkboxes)
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
  title.textContent = 'Choose Your Installer(s)';
  title.style.cssText = 'margin: 0 0 16px 0; font-size: 24px; color: #08363f;';
  modalContent.appendChild(title);

  const subtitle = document.createElement('p');
  subtitle.textContent = 'Select which installers you\'d like to get quotes from (you can pick multiple):';
  subtitle.style.cssText = 'color: #1a3d42; margin-bottom: 20px; font-size: 14px;';
  modalContent.appendChild(subtitle);

  const list = document.createElement('div');
  list.style.cssText = 'margin-bottom: 20px;';
  const selectedInstallers = [];

  installers.forEach((installer, idx) => {
    const checkboxId = `installer-checkbox-${idx}`;
    const item = document.createElement('label');
    item.style.cssText = `
      display: flex;
      align-items: flex-start;
      padding: 16px;
      margin-bottom: 8px;
      border: 2px solid #d9d0c1;
      border-radius: 8px;
      background: white;
      cursor: pointer;
      transition: all 0.2s;
    `;

    item.onmouseover = () => item.style.borderColor = '#d4751c';
    item.onmouseout = () => item.style.borderColor = '#d9d0c1';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = checkboxId;
    checkbox.style.cssText = 'margin-top: 2px; margin-right: 12px; cursor: pointer;';
    checkbox.onchange = () => {
      if (checkbox.checked) {
        if (!selectedInstallers.find(s => s.name === installer.name)) {
          selectedInstallers.push(installer);
        }
      } else {
        const idx = selectedInstallers.findIndex(s => s.name === installer.name);
        if (idx > -1) selectedInstallers.splice(idx, 1);
      }
    };

    const content = document.createElement('div');
    content.style.cssText = 'flex: 1;';

    const name = document.createElement('div');
    name.style.cssText = 'font-weight: 600; color: #08363f; margin-bottom: 4px;';
    name.textContent = installer.name;

    const details = document.createElement('div');
    details.style.cssText = 'font-size: 13px; color: #1a3d42;';
    details.textContent = `${installer.specialty} • ${installer.rating}★ (${installer.reviews} reviews)`;

    const contact = document.createElement('div');
    contact.style.cssText = 'font-size: 12px; color: #6b7d80; margin-top: 4px;';
    contact.textContent = installer.phone;

    content.appendChild(name);
    content.appendChild(details);
    content.appendChild(contact);

    item.appendChild(checkbox);
    item.appendChild(content);
    list.appendChild(item);
  });

  modalContent.appendChild(list);

  const buttonContainer = document.createElement('div');
  buttonContainer.style.cssText = 'display: flex; gap: 12px;';

  const submitBtn = document.createElement('button');
  submitBtn.type = 'button';
  submitBtn.textContent = 'Send Requests';
  submitBtn.style.cssText = `
    flex: 1;
    padding: 12px;
    border: none;
    background: #d4751c;
    border-radius: 8px;
    cursor: pointer;
    color: white;
    font-weight: 600;
  `;
  submitBtn.onclick = () => {
    if (selectedInstallers.length === 0) {
      alert('Please select at least one installer');
      return;
    }
    modal.remove();
    onSelect(selectedInstallers);
  };

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

  buttonContainer.appendChild(submitBtn);
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
    // Pre-fill email from localStorage if available (from previous step)
    const storedEmail = localStorage.getItem('hpr_lead_email');
    const emailInputs = matchForm.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
      if (storedEmail) input.value = storedEmail;
    });

    // Add name attributes
    const firstNameInput = matchForm.querySelector('input[placeholder="First name"]');
    if (firstNameInput && !firstNameInput.name) firstNameInput.name = 'firstname';

    const phoneInput = matchForm.querySelector('input[type="tel"]');
    if (phoneInput && !phoneInput.name) phoneInput.name = 'phone';

    matchForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Get city from URL (city pages) or from form data (homepage)
      let cityName = null;

      // Try to get city from URL first (city pages: /ca/bc/vancouver)
      const cityMatch = window.location.pathname.match(/\/ca\/bc\/([a-z-]+)/);
      if (cityMatch) {
        const citySlug = cityMatch[1];
        cityName = citySlug.replace('-', ' ');
      }

      // If not in URL, check if city is stored in form or localStorage (homepage)
      if (!cityName) {
        const formCity = matchForm.querySelector('input[name="city"]');
        if (formCity) {
          cityName = formCity.value;
        } else {
          // Try to get from page's city selector (homepage calculator)
          const citySelect = document.getElementById('hpr-city');
          if (citySelect) {
            cityName = citySelect.value;
          }
        }
      }

      if (!cityName) {
        showMessage(matchForm, '✗ Could not detect your city. Please enter your city or select from the dropdown.', false);
        return;
      }

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

      // Show installer chooser (now with multi-select support)
      showInstallerChooser(
        installers,
        async (selectedInstallers) => {
          // Collect form data
          const formData = new FormData(matchForm);
          const data = Object.fromEntries(formData);

          // Use stored email (should be from first form step)
          if (!data.email) {
            data.email = localStorage.getItem('hpr_lead_email');
          }

          // Validate email exists
          if (!data.email) {
            showMessage(matchForm, '✗ Please enter your email first.', false);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Match me with my installer →';
            return;
          }

          // Validate email format
          if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
            showMessage(matchForm, '✗ Please enter a valid email address.', false);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Match me with my installer →';
            return;
          }

          // Add city and page context (shared for all submissions)
          data.city = cityName;
          data.page_url = window.location.href;

          submitBtn.disabled = true;
          submitBtn.textContent = `Sending to ${selectedInstallers.length} installer${selectedInstallers.length !== 1 ? 's' : ''}...`;

          let successCount = 0;
          let failCount = 0;

          // Submit to each selected installer in parallel
          const submissions = selectedInstallers.map(installer =>
            fetch(`${WORKER_URL}/estimate-lead`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                ...data,
                installer_name: installer.name,
                installer_email: installer.email || '',
                installer_phone: installer.phone || ''
              })
            })
              .then(response => response.json())
              .then(result => {
                if (result.success) successCount++;
                else failCount++;
              })
              .catch(() => failCount++)
          );

          try {
            await Promise.allSettled(submissions);

            if (successCount > 0) {
              const msg = successCount === 1
                ? `✓ Perfect! We've sent your details to ${selectedInstallers[0].name}.`
                : `✓ Perfect! We've sent your details to ${successCount} installers.`;
              showMessage(matchForm, msg, true);
              matchForm.reset();
            } else {
              showMessage(matchForm, '✗ Could not submit to any installers. Please try again.', false);
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

      // Store email in localStorage for next step (installer match)
      if (data.email) {
        localStorage.setItem('hpr_lead_email', data.email);
      }
      if (data.firstname) {
        localStorage.setItem('hpr_lead_firstname', data.firstname);
      }

      try {
        const response = await fetch(`${WORKER_URL}/newsletter`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });

        if (response.ok) {
          showMessage(emailForm, '✓ Got it! Check your email for your breakdown.', true);
          // Don't reset - keep data for next step
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

(() => {
  'use strict';

  // ============================================================
  // JAM SETTINGS POLISH
  // Salary converter only. Existing JAM salary targets remain intact.
  // ============================================================

  const NET_FROM_GROSS_RATIO = 0.78;
  const MONTHS_PER_YEAR = 12;

  let initialized = false;
  let internalUpdate = false;

  const IDS = {
    monthlyNet: 'salaryMonthlyNet',
    monthlyGross: 'salaryMonthlyGross',
    annualNet: 'salaryAnnualNet',
    annualGross: 'salaryAnnualGross'
  };

  function element(key) {
    return document.getElementById(IDS[key]);
  }

  function parseAmount(value) {
    const number = Number.parseFloat(
      String(value ?? '')
        .replace(/\s/g, '')
        .replace(',', '.')
    );

    return Number.isFinite(number) && number >= 0
      ? number
      : null;
  }

  function rounded(value) {
    if (!Number.isFinite(value)) {
      return '';
    }

    return String(
      Math.round(value)
    );
  }

  function valuesFrom(key, amount) {
    let monthlyGross;

    switch (key) {
      case 'monthlyNet':
        monthlyGross =
          amount / NET_FROM_GROSS_RATIO;
        break;

      case 'monthlyGross':
        monthlyGross =
          amount;
        break;

      case 'annualNet':
        monthlyGross =
          amount /
          MONTHS_PER_YEAR /
          NET_FROM_GROSS_RATIO;
        break;

      case 'annualGross':
        monthlyGross =
          amount /
          MONTHS_PER_YEAR;
        break;

      default:
        return null;
    }

    const monthlyNet =
      monthlyGross *
      NET_FROM_GROSS_RATIO;

    return {
      monthlyNet,
      monthlyGross,
      annualNet:
        monthlyNet *
        MONTHS_PER_YEAR,
      annualGross:
        monthlyGross *
        MONTHS_PER_YEAR
    };
  }

  function applyConvertedValues(
    sourceKey,
    amount
  ) {
    const converted =
      valuesFrom(
        sourceKey,
        amount
      );

    if (!converted) {
      return;
    }

    internalUpdate = true;

    for (
      const [
        key,
        value
      ]
      of Object.entries(converted)
    ) {
      const input =
        element(key);

      if (
        input &&
        key !== sourceKey
      ) {
        input.value =
          rounded(value);
      }
    }

    internalUpdate = false;
  }

  function clearOtherFields(
    sourceKey
  ) {
    internalUpdate = true;

    for (
      const key
      of Object.keys(IDS)
    ) {
      if (
        key !== sourceKey
      ) {
        const input =
          element(key);

        if (input) {
          input.value = '';
        }
      }
    }

    internalUpdate = false;
  }

  function onSalaryInput(
    key,
    event
  ) {
    if (internalUpdate) {
      return;
    }

    const amount =
      parseAmount(
        event.target.value
      );

    if (amount === null) {
      if (
        !String(
          event.target.value
        ).trim()
      ) {
        clearOtherFields(key);
      }

      return;
    }

    applyConvertedValues(
      key,
      amount
    );
  }

  async function persistConverter() {
    if (
      typeof api !== 'function'
    ) {
      return;
    }

    const values = {
      salary_converter_monthly_net:
        element('monthlyNet')?.value.trim() || '',

      salary_converter_monthly_gross:
        element('monthlyGross')?.value.trim() || '',

      salary_converter_annual_net:
        element('annualNet')?.value.trim() || '',

      salary_converter_annual_gross:
        element('annualGross')?.value.trim() || ''
    };

    try {
      await Promise.all(
        Object.entries(values)
          .map(
            ([key, value]) =>
              api(
                'save_setting',
                key,
                value
              )
          )
      );
    } catch (error) {
      console.error(
        'Could not save salary converter settings.',
        error
      );
    }
  }

  async function restoreConverter() {
    if (
      typeof api !== 'function'
    ) {
      return;
    }

    try {
      const result =
        await api(
          'bootstrap'
        );

      const settings =
        result?.settings || {};

      const saved = {
        monthlyNet:
          settings.salary_converter_monthly_net || '',

        monthlyGross:
          settings.salary_converter_monthly_gross || '',

        annualNet:
          settings.salary_converter_annual_net || '',

        annualGross:
          settings.salary_converter_annual_gross || ''
      };

      for (
        const [
          key,
          value
        ]
        of Object.entries(saved)
      ) {
        const input =
          element(key);

        if (input) {
          input.value =
            value;
        }
      }

      // Recalculate from the first saved value so all four remain coherent.
      for (
        const key
        of [
          'monthlyNet',
          'monthlyGross',
          'annualNet',
          'annualGross'
        ]
      ) {
        const amount =
          parseAmount(
            saved[key]
          );

        if (amount !== null) {
          applyConvertedValues(
            key,
            amount
          );
          break;
        }
      }
    } catch (error) {
      console.error(
        'Could not restore salary converter settings.',
        error
      );
    }
  }

  function decorateNumberSteppers() {
    const inputs =
      document.querySelectorAll(
        '#settingsPage input[type="number"]'
      );

    inputs.forEach(
      input => {
        if (
          input.parentElement?.classList.contains(
            'salary-number-stepper'
          )
        ) {
          return;
        }

        const wrapper =
          document.createElement(
            'div'
          );

        wrapper.className =
          'salary-number-stepper';

        const minus =
          document.createElement(
            'button'
          );

        minus.type =
          'button';

        minus.className =
          'salary-step-btn salary-step-minus';

        minus.textContent =
          '−';

        minus.setAttribute(
          'aria-label',
          'Decrease'
        );

        const plus =
          document.createElement(
            'button'
          );

        plus.type =
          'button';

        plus.className =
          'salary-step-btn salary-step-plus';

        plus.textContent =
          '+';

        plus.setAttribute(
          'aria-label',
          'Increase'
        );

        const parent =
          input.parentNode;

        parent.insertBefore(
          wrapper,
          input
        );

        wrapper.appendChild(
          minus
        );

        wrapper.appendChild(
          input
        );

        wrapper.appendChild(
          plus
        );

        const applyStep =
          direction => {
            if (direction < 0) {
              input.stepDown();
            } else {
              input.stepUp();
            }

            input.dispatchEvent(
              new Event(
                'input',
                {
                  bubbles: true
                }
              )
            );

            input.dispatchEvent(
              new Event(
                'change',
                {
                  bubbles: true
                }
              )
            );

            input.focus();
          };

        minus.addEventListener(
          'click',
          () => applyStep(-1)
        );

        plus.addEventListener(
          'click',
          () => applyStep(1)
        );
      }
    );
  }

  function bindConverter() {
    for (
      const key
      of Object.keys(IDS)
    ) {
      const input =
        element(key);

      if (!input) {
        continue;
      }

      input.addEventListener(
        'input',
        event =>
          onSalaryInput(
            key,
            event
          )
      );
    }

    const saveButton =
      document.getElementById(
        'saveSettingsBtn'
      );

    if (saveButton) {
      saveButton.addEventListener(
        'click',
        persistConverter
      );
    }
  }

  async function init() {
    if (initialized) {
      return;
    }

    initialized = true;

    decorateNumberSteppers();

    bindConverter();

    await restoreConverter();
  }

  document.addEventListener(
    'pywebviewready',
    init
  );

  window.setTimeout(
    () => {
      if (
        !initialized &&
        window.pywebview?.api
      ) {
        init();
      }
    },
    100
  );
})();

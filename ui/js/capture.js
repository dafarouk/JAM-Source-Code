const STATUSES = [
  'Saved',
  'To Review',
  'Applied',
  'Interviewing',
  'Offer',
  'Accepted',
  'Rejected',
  'Withdrawn',
  'Archived'
];

let draftStartedAt = null;
let initialized = false;

const $ = selector =>
  document.querySelector(selector);

async function api(
  method,
  ...args
) {
  const fn =
    window.pywebview?.api?.[method];

  if (!fn) {
    throw new Error(
      'JAM backend is not ready yet.'
    );
  }

  const result =
    await fn(...args);

  if (!result?.ok) {
    throw new Error(
      result?.error ||
      'Unknown JAM error.'
    );
  }

  return result;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function toast(
  message,
  type = 'success'
) {
  const node = $('#toast');

  node.textContent = message;

  node.className =
    `toast ${
      type === 'error'
        ? 'error'
        : ''
    }`;

  node.hidden = false;

  clearTimeout(
    toast.timer
  );

  toast.timer =
    setTimeout(
      () => {
        node.hidden = true;
      },
      2600
    );
}

function fillStatuses() {
  $('#status').innerHTML =
    STATUSES
      .map(
        status => `
          <option value="${status}">
            ${status}
          </option>
        `
      )
      .join('');

  $('#status').value =
    'Saved';
}

function payload() {
  return {
    company:
      $('#company')
        .value
        .trim(),

    job_title:
      $('#jobTitle')
        .value
        .trim(),

    location:
      $('#location')
        .value
        .trim(),

    status:
      $('#status')
        .value,

    url:
      $('#jobUrl')
        .value
        .trim(),

    description:
      $('#description')
        .value
        .trim(),

    source:
      $('#source')
        .value
        .trim(),

    rating:
      Number(
        $('#rating')
          .value || 0
      ),

    notes:
      $('#notes')
        .value
        .trim(),

    date_saved:
      draftStartedAt ||
      new Date()
        .toISOString()
  };
}

function clearForm() {
  [
    'company',
    'jobTitle',
    'location',
    'jobUrl',
    'description',
    'source',
    'notes'
  ]
    .forEach(
      id => {
        $(`#${id}`).value = '';
      }
    );

  $('#status').value =
    'Saved';

  $('#rating').value =
    '0';

  draftStartedAt =
    null;

  $('#company').focus();
}

async function saveJob() {
  try {
    const data =
      payload();

    if (
      !data.company &&
      !data.job_title
    ) {
      throw new Error(
        'Add at least a company or job title.'
      );
    }

    await api(
      'save_application',
      data
    );

    clearForm();

    toast(
      'Saved. Ready for the next job.'
    );

  } catch (error) {
    toast(
      error.message,
      'error'
    );
  }
}

function chips(
  values,
  cls
) {
  if (!values?.length) {
    return `
      <span
        style="
          color:#8993A3;
          font-size:11px
        "
      >
        None detected
      </span>
    `;
  }

  return `
    <div class="chips">
      ${
        values
          .map(
            value => `
              <span
                class="chip ${cls}"
              >
                ${escapeHtml(value)}
              </span>
            `
          )
          .join('')
      }
    </div>
  `;
}

function showLoading() {
  const overlay =
    $('#overlay');

  overlay.hidden =
    false;

  overlay.innerHTML = `
    <div
      class="analysis-card"
      style="text-align:center"
    >
      <div class="analysis-kicker">
        JAM MATCH ENGINE
      </div>

      <h2>
        Analyzing…
      </h2>

      <div class="spinner"></div>

      <p
        id="analysisStep"
        style="
          color:#AEB6C2;
          font-size:11px
        "
      >
        Reading job requirements…
      </p>
    </div>
  `;

  const steps = [
    'Reading job requirements…',
    'Reading your selected CV…',
    'Comparing skills and experience…',
    'Building your match result…'
  ];

  let index = 0;

  return setInterval(
    () => {
      index =
        (index + 1) %
        steps.length;

      const node =
        $('#analysisStep');

      if (node) {
        node.textContent =
          steps[index];
      }
    },
    650
  );
}

function showResult(
  analysis
) {
  const overlay =
    $('#overlay');

  const experience =
    analysis.required_years == null
      ? 'No explicit minimum detected'
      : `Job: ${
          analysis.required_years
        }+ year(s) • CV detected: ${
          analysis.cv_years == null
            ? 'unclear'
            : analysis.cv_years
        }`;

  overlay.hidden =
    false;

  overlay.innerHTML = `
    <div class="analysis-card">

      <div class="analysis-kicker">
        CV MATCH RESULT
      </div>

      <h2>
        ${analysis.score}% match
      </h2>

      <div
        class="score-ring"
        style="--score:${analysis.score}"
      >
        <strong>
          ${analysis.score}%
        </strong>
      </div>

      <div class="result-group">
        <strong>
          Matched tools & skills
        </strong>

        ${
          chips(
            analysis.matched_skills,
            'good'
          )
        }
      </div>

      <div class="result-group">
        <strong>
          Missing / not clearly found
        </strong>

        ${
          chips(
            analysis.missing_skills,
            'missing'
          )
        }
      </div>

      <div class="result-group">
        <strong>
          Experience
        </strong>

        <p>
          ${escapeHtml(experience)}
        </p>
      </div>

      <div class="result-group">
        <strong>
          What to review
        </strong>

        <p>
          ${
            analysis.suggestions
              .map(escapeHtml)
              .join('<br><br>')
          }
        </p>
      </div>

      <button
        class="btn gold result-close"
        id="closeResultBtn"
      >
        Done
      </button>

    </div>
  `;

  $('#closeResultBtn')
    .onclick =
    () => {
      overlay.hidden = true;
      overlay.innerHTML = '';
    };
}

async function analyzeJob() {
  const data =
    payload();

  if (
    !data.job_title &&
    !data.description
  ) {
    toast(
      'Add a job title or description first.',
      'error'
    );

    return;
  }

  const timer =
    showLoading();

  try {
    const result =
      await api(
        'analyze_job',
        data
      );

    clearInterval(timer);

    showResult(
      result.analysis
    );

  } catch (error) {
    clearInterval(timer);

    $('#overlay').hidden =
      true;

    $('#overlay').innerHTML =
      '';

    toast(
      error.message,
      'error'
    );
  }
}

async function changeCorner() {
  try {
    await api(
      'move_capture_window',
      $('#cornerSelect').value
    );

  } catch (error) {
    toast(
      error.message,
      'error'
    );
  }
}

async function closeCapture() {
  $('#closeCaptureBtn').disabled =
    true;

  try {
    await api(
      'close_capture_window'
    );

  } catch (error) {
    $('#closeCaptureBtn').disabled =
      false;

    toast(
      error.message,
      'error'
    );
  }
}

async function init() {
  if (initialized) {
    return;
  }

  initialized =
    true;

  fillStatuses();

  try {
    const boot =
      await api('bootstrap');

    $('#cornerSelect').value =
      boot.settings?.capture_corner ||
      'top-right';

  } catch (_) {
  }

  document
    .querySelectorAll(
      '.draft-trigger'
    )
    .forEach(
      input =>
        input.addEventListener(
          'input',
          () => {
            if (
              !draftStartedAt &&
              String(
                input.value
              ).trim()
            ) {
              draftStartedAt =
                new Date()
                  .toISOString();
            }
          }
        )
    );

  $('#saveBtn').onclick =
    saveJob;

  $('#analyzeBtn').onclick =
    analyzeJob;

  $('#cornerSelect').onchange =
    changeCorner;

  $('#closeCaptureBtn').onclick =
    closeCapture;

  $('#company').focus();
}

document.addEventListener(
  'pywebviewready',
  init
);

window.addEventListener(
  'DOMContentLoaded',
  () =>
    setTimeout(
      () => {
        if (
          window.pywebview?.api
        ) {
          init();
        }
      },
      100
    )
);
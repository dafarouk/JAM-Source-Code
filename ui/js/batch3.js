(() => {
  'use strict';

  let initialized = false;

  function tr(text) {
    return window.JAM_I18N?.translate
      ? window.JAM_I18N.translate(text)
      : text;
  }

  function fmtDateTime(value) {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString(
      window.JAM_I18N?.language === 'fr' ? 'fr-FR' : 'en-GB',
      {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }
    );
  }

  function selectedApplicationId() {
    if (state.selectedIds.size !== 1) return null;
    return Number([...state.selectedIds][0]);
  }

  function contactMarkup(item) {
    const parts = [item.role, item.email, item.phone]
      .filter(Boolean)
      .map(value => `<span>${escapeHtml(value)}</span>`)
      .join('');

    return `
      <div class="tracking-entry">
        <div class="tracking-entry-main">
          <strong>${escapeHtml(item.name || tr('Unnamed contact'))}</strong>
          <div class="tracking-meta">${parts || `<span>${escapeHtml(tr('No extra contact details'))}</span>`}</div>
          ${item.note ? `<div class="tracking-note-preview">${escapeHtml(item.note)}</div>` : ''}
          ${item.is_primary ? `<span class="tracking-badge">${escapeHtml(tr('Imported primary contact'))}</span>` : ''}
        </div>
        <div class="tracking-actions">
          ${item.url ? `<button class="btn secondary" data-contact-open="${item.id}">${escapeHtml(tr('Open'))}</button>` : ''}
          <button class="btn secondary" data-contact-edit="${item.id}">${escapeHtml(tr('Edit'))}</button>
          <button class="btn danger subtle" data-contact-delete="${item.id}">${escapeHtml(tr('Remove'))}</button>
        </div>
      </div>
    `;
  }

  function noteMarkup(item) {
    return `
      <div class="tracking-entry tracking-note-entry">
        <div class="tracking-entry-main">
          <small>${escapeHtml(fmtDateTime(item.created_at))}</small>
          <div class="tracking-note-text">${escapeHtml(item.note_text || '')}</div>
          ${item.updated_at && item.updated_at !== item.created_at ? `<span class="tracking-edited">${escapeHtml(tr('Edited'))}</span>` : ''}
        </div>
        <div class="tracking-actions">
          <button class="btn secondary" data-note-edit="${item.id}">${escapeHtml(tr('Edit'))}</button>
          <button class="btn danger subtle" data-note-delete="${item.id}">${escapeHtml(tr('Remove'))}</button>
        </div>
      </div>
    `;
  }

  function attachmentMarkup(item) {
    return `
      <div class="tracking-entry">
        <div class="tracking-entry-main">
          <strong>${escapeHtml(item.file_name || tr('Attachment'))}</strong>
          <div class="tracking-meta">
            <span>${escapeHtml(item.category || tr('Other'))}</span>
            <span>${escapeHtml(fmtDateTime(item.created_at))}</span>
            ${item.exists ? '' : `<span class="tracking-missing">${escapeHtml(tr('File missing'))}</span>`}
          </div>
        </div>
        <div class="tracking-actions">
          <button class="btn secondary" data-attachment-open="${item.id}" ${item.exists ? '' : 'disabled'}>${escapeHtml(tr('Open'))}</button>
          <button class="btn secondary" data-attachment-folder="${item.id}" ${item.exists ? '' : 'disabled'}>${escapeHtml(tr('Folder'))}</button>
          <button class="btn danger subtle" data-attachment-delete="${item.id}">${escapeHtml(tr('Remove'))}</button>
        </div>
      </div>
    `;
  }

  function statusTimelineMarkup(history) {
    if (!history?.length) {
      return `<p class="muted">${escapeHtml(tr('No status history yet.'))}</p>`;
    }

    return history.map(item => `
      <div class="timeline-item">
        <span>${statusPill(item.status)}</span>
        <small>${escapeHtml(fmtDateTime(item.changed_at))}</small>
      </div>
    `).join('');
  }

  async function showTrackingDetails(applicationId) {
    try {
      const [detailsResult, trackingResult] = await Promise.all([
        api('get_application_details', Number(applicationId)),
        api('get_application_tracking', Number(applicationId))
      ]);

      const app = detailsResult.application;
      const tracking = trackingResult.tracking || {};
      const contacts = tracking.contacts || [];
      const notes = tracking.notes || [];
      const attachments = tracking.attachments || [];

      const body = `
        <div class="tracking-summary">
          <div><span>${escapeHtml(tr('Company'))}</span><strong>${escapeHtml(app.company || '—')}</strong></div>
          <div><span>${escapeHtml(tr('Job title'))}</span><strong>${escapeHtml(app.job_title || '—')}</strong></div>
          <div><span>${escapeHtml(tr('Status'))}</span>${statusPill(app.status)}</div>
          <div><span>${escapeHtml(tr('Score'))}</span><strong>${app.match_score == null ? '—' : `${app.match_score}%`}</strong></div>
        </div>

        <div class="tracking-section">
          <div class="tracking-section-head">
            <div><span class="eyebrow">${escapeHtml(tr('CONTACTS'))}</span><h3>${escapeHtml(tr('Contacts'))}</h3></div>
            <button class="btn gold" data-add-contact>+ ${escapeHtml(tr('Add contact'))}</button>
          </div>
          <div class="tracking-list">
            ${contacts.length ? contacts.map(contactMarkup).join('') : `<p class="muted">${escapeHtml(tr('No contacts yet.'))}</p>`}
          </div>
        </div>

        <div class="tracking-section">
          <div class="tracking-section-head">
            <div><span class="eyebrow">${escapeHtml(tr('NOTES HISTORY'))}</span><h3>${escapeHtml(tr('Notes history'))}</h3></div>
            <button class="btn gold" data-add-note>+ ${escapeHtml(tr('Add note'))}</button>
          </div>
          <div class="tracking-list">
            ${notes.length ? notes.map(noteMarkup).join('') : `<p class="muted">${escapeHtml(tr('No notes yet.'))}</p>`}
          </div>
        </div>

        <div class="tracking-section">
          <div class="tracking-section-head">
            <div><span class="eyebrow">${escapeHtml(tr('ATTACHMENTS'))}</span><h3>${escapeHtml(tr('Attachments'))}</h3></div>
            <div class="tracking-attachment-add">
              <select class="control" data-attachment-category>
                <option>${escapeHtml(tr('CV'))}</option>
                <option>${escapeHtml(tr('Cover letter'))}</option>
                <option>${escapeHtml(tr('Screenshot'))}</option>
                <option>${escapeHtml(tr('Other'))}</option>
              </select>
              <button class="btn gold" data-add-attachment>+ ${escapeHtml(tr('Add file'))}</button>
            </div>
          </div>
          <p class="muted tracking-local-note">${escapeHtml(tr('Attachments are copied into JAM local storage.'))}</p>
          <div class="tracking-list">
            ${attachments.length ? attachments.map(attachmentMarkup).join('') : `<p class="muted">${escapeHtml(tr('No attachments yet.'))}</p>`}
          </div>
        </div>

        <div class="tracking-section">
          <div class="tracking-section-head"><div><span class="eyebrow">${escapeHtml(tr('ACTIVITY'))}</span><h3>${escapeHtml(tr('Status history'))}</h3></div></div>
          <div class="status-timeline">${statusTimelineMarkup(app.status_history || [])}</div>
        </div>
      `;

      const root = openModal({
        kicker: 'APPLICATION TRACKING',
        title: `${app.company || ''} • ${app.job_title || ''}`,
        body,
        actions: `
          <button class="btn secondary" data-tracking-close>${escapeHtml(tr('Close'))}</button>
          <button class="btn gold" data-tracking-edit-app>${escapeHtml(tr('Edit application'))}</button>
        `,
        wide: true
      });

      $('[data-tracking-close]', root).onclick = closeModal;
      $('[data-tracking-edit-app]', root).onclick = () => {
        closeModal();
        openJobModal(app);
      };

      $('[data-add-contact]', root).onclick = () => openContactEditor(applicationId, null);
      $('[data-add-note]', root).onclick = () => openNoteEditor(applicationId, null);
      $('[data-add-attachment]', root).onclick = async () => {
        try {
          const category = $('[data-attachment-category]', root)?.value || 'Other';
          const result = await api('add_application_attachment', Number(applicationId), category);
          if (!result.cancelled) {
            toast(tr('Attachment added.'), 'success');
            await showTrackingDetails(applicationId);
          }
        } catch (error) {
          toast(error.message, 'error');
        }
      };

      $$('[data-contact-open]', root).forEach(button => {
        button.onclick = async () => {
          const item = contacts.find(row => Number(row.id) === Number(button.dataset.contactOpen));
          if (item?.url) await api('open_url', item.url).catch(error => toast(error.message, 'error'));
        };
      });
      $$('[data-contact-edit]', root).forEach(button => {
        button.onclick = () => {
          const item = contacts.find(row => Number(row.id) === Number(button.dataset.contactEdit));
          if (item) openContactEditor(applicationId, item);
        };
      });
      $$('[data-contact-delete]', root).forEach(button => {
        button.onclick = async () => {
          try {
            await api('delete_application_contact', Number(applicationId), Number(button.dataset.contactDelete));
            await showTrackingDetails(applicationId);
          } catch (error) { toast(error.message, 'error'); }
        };
      });

      $$('[data-note-edit]', root).forEach(button => {
        button.onclick = () => {
          const item = notes.find(row => Number(row.id) === Number(button.dataset.noteEdit));
          if (item) openNoteEditor(applicationId, item);
        };
      });
      $$('[data-note-delete]', root).forEach(button => {
        button.onclick = async () => {
          try {
            await api('delete_application_note', Number(applicationId), Number(button.dataset.noteDelete));
            await showTrackingDetails(applicationId);
          } catch (error) { toast(error.message, 'error'); }
        };
      });

      $$('[data-attachment-open]', root).forEach(button => {
        button.onclick = async () => {
          const item = attachments.find(row => Number(row.id) === Number(button.dataset.attachmentOpen));
          if (item?.stored_path) await api('open_path', item.stored_path).catch(error => toast(error.message, 'error'));
        };
      });
      $$('[data-attachment-folder]', root).forEach(button => {
        button.onclick = async () => {
          const item = attachments.find(row => Number(row.id) === Number(button.dataset.attachmentFolder));
          if (item?.stored_path) await api('open_parent_folder', item.stored_path).catch(error => toast(error.message, 'error'));
        };
      });
      $$('[data-attachment-delete]', root).forEach(button => {
        button.onclick = async () => {
          try {
            await api('delete_application_attachment', Number(applicationId), Number(button.dataset.attachmentDelete));
            await showTrackingDetails(applicationId);
          } catch (error) { toast(error.message, 'error'); }
        };
      });
    } catch (error) {
      toast(error.message, 'error');
    }
  }

  function openContactEditor(applicationId, contact) {
    const edit = Boolean(contact);
    const body = `
      <div class="tracking-form-grid">
        <label>${escapeHtml(tr('Name'))}<input class="control full" data-contact-name value="${escapeHtml(contact?.name || '')}"></label>
        <label>${escapeHtml(tr('Role'))}<input class="control full" data-contact-role value="${escapeHtml(contact?.role || '')}" placeholder="Recruiter, Hiring Manager..."></label>
        <label>${escapeHtml(tr('Email'))}<input class="control full" type="email" data-contact-email value="${escapeHtml(contact?.email || '')}"></label>
        <label>${escapeHtml(tr('Phone'))}<input class="control full" data-contact-phone value="${escapeHtml(contact?.phone || '')}"></label>
        <label class="tracking-span-2">${escapeHtml(tr('Link'))}<input class="control full" data-contact-url value="${escapeHtml(contact?.url || '')}" placeholder="https://..."></label>
        <label class="tracking-span-2">${escapeHtml(tr('Note'))}<textarea class="control full" data-contact-note>${escapeHtml(contact?.note || '')}</textarea></label>
      </div>
    `;
    const root = openModal({
      kicker: edit ? 'EDIT CONTACT' : 'NEW CONTACT',
      title: edit ? tr('Edit contact') : tr('Add contact'),
      body,
      actions: `<button class="btn secondary" data-contact-cancel>${escapeHtml(tr('Cancel'))}</button><button class="btn gold" data-contact-save>${escapeHtml(tr('Save'))}</button>`
    });
    $('[data-contact-cancel]', root).onclick = () => showTrackingDetails(applicationId);
    $('[data-contact-save]', root).onclick = async () => {
      const payload = {
        name: $('[data-contact-name]', root).value.trim(),
        role: $('[data-contact-role]', root).value.trim(),
        email: $('[data-contact-email]', root).value.trim(),
        phone: $('[data-contact-phone]', root).value.trim(),
        url: $('[data-contact-url]', root).value.trim(),
        note: $('[data-contact-note]', root).value.trim()
      };
      try {
        if (edit) {
          await api('update_application_contact', Number(contact.id), payload);
        } else {
          await api('add_application_contact', Number(applicationId), payload);
        }
        await showTrackingDetails(applicationId);
      } catch (error) { toast(error.message, 'error'); }
    };
  }

  function openNoteEditor(applicationId, note) {
    const edit = Boolean(note);
    const root = openModal({
      kicker: edit ? 'EDIT NOTE' : 'NEW NOTE',
      title: edit ? tr('Edit note') : tr('Add note'),
      body: `<label>${escapeHtml(tr('Note'))}<textarea class="control full tracking-note-editor" data-note-text>${escapeHtml(note?.note_text || '')}</textarea></label>`,
      actions: `<button class="btn secondary" data-note-cancel>${escapeHtml(tr('Cancel'))}</button><button class="btn gold" data-note-save>${escapeHtml(tr('Save'))}</button>`
    });
    $('[data-note-cancel]', root).onclick = () => showTrackingDetails(applicationId);
    $('[data-note-save]', root).onclick = async () => {
      const value = $('[data-note-text]', root).value.trim();
      try {
        if (edit) {
          await api('update_application_note', Number(applicationId), Number(note.id), value);
        } else {
          await api('add_application_note', Number(applicationId), value);
        }
        await showTrackingDetails(applicationId);
      } catch (error) { toast(error.message, 'error'); }
    };
  }

  function injectTrackingButton() {
    if ($('#trackingSelectedBtn')) return;
    const editButton = $('#editSelectedBtn');
    if (!editButton?.parentElement) return;

    const button = document.createElement('button');
    button.id = 'trackingSelectedBtn';
    button.className = 'btn secondary';
    button.hidden = true;
    button.textContent = tr('Tracking');
    button.onclick = () => {
      const id = selectedApplicationId();
      if (id) showTrackingDetails(id);
    };
    editButton.insertAdjacentElement('afterend', button);
  }

  function syncTrackingSelection() {
    const button = $('#trackingSelectedBtn');
    if (button) button.hidden = state.selectedIds.size !== 1;
  }

  function wrapSelectionUi() {
    const original = window.updateSelectionUi;
    if (typeof original !== 'function' || original.__batch3Wrapped) return;
    const wrapped = function(...args) {
      const result = original(...args);
      syncTrackingSelection();
      return result;
    };
    wrapped.__batch3Wrapped = true;
    window.updateSelectionUi = wrapped;
    try { updateSelectionUi = wrapped; } catch (_) {}
  }

  async function saveSetting(key, value) {
    const result = await api('save_setting', key, String(value));
    state.settings[key] = String(value);
    return result;
  }


  function layoutPrimaryContactFields(form) {
    if (!form || form.querySelector('[data-primary-contact-layout]')) {
      return;
    }

    const nameInput =
      form.querySelector(
        '[name="contact_name"]'
      );

    const urlInput =
      form.querySelector(
        '[name="contact_url"]'
      );

    const nameLabel =
      nameInput?.closest(
        'label'
      );

    const urlLabel =
      urlInput?.closest(
        'label'
      );

    if (
      !nameInput ||
      !urlInput ||
      !nameLabel ||
      !urlLabel
    ) {
      return;
    }

    const block =
      document.createElement(
        'div'
      );

    block.className =
      'job-primary-contact-block job-editor-span-2';

    block.dataset.primaryContactLayout =
      '1';

    const fields =
      document.createElement(
        'div'
      );

    fields.className =
      'job-primary-contact-fields';

    nameLabel.parentElement.insertBefore(
      block,
      nameLabel
    );

    block.appendChild(
      fields
    );

    fields.appendChild(
      nameLabel
    );

    fields.appendChild(
      urlLabel
    );

    const openButton =
      urlLabel.querySelector(
        '.job-inline-open'
      );

    if (openButton) {
      const actions =
        document.createElement(
          'div'
        );

      actions.className =
        'job-primary-contact-actions';

      block.appendChild(
        actions
      );

      actions.appendChild(
        openButton
      );
    }
  }

  function editorContactMarkup(item) {
    const details =
      [
        item.role,
        item.email,
        item.phone
      ]
        .filter(Boolean)
        .map(
          value =>
            `<span>${escapeHtml(value)}</span>`
        )
        .join('');

    return `
      <div
        class="job-tracking-row"
        data-inline-contact-row="${item.id}"
      >
        <div class="job-tracking-row-main">
          <strong>
            ${escapeHtml(
              item.name ||
              tr('Unnamed contact')
            )}
          </strong>

          <div class="tracking-meta">
            ${
              details ||
              `<span>${escapeHtml(
                tr('No extra contact details')
              )}</span>`
            }
          </div>

          ${
            item.url
              ? `<div class="job-tracking-link">${escapeHtml(item.url)}</div>`
              : ''
          }

          ${
            item.note
              ? `<div class="tracking-note-preview">${escapeHtml(item.note)}</div>`
              : ''
          }

          ${
            item.is_primary
              ? `<span class="tracking-badge">${escapeHtml(
                  tr('Imported primary contact')
                )}</span>`
              : ''
          }
        </div>

        <div class="job-tracking-row-actions">
          ${
            item.url
              ? `<button type="button" class="btn secondary" data-editor-contact-open="${item.id}">${escapeHtml(tr('Open'))}</button>`
              : ''
          }

          <button
            type="button"
            class="btn secondary"
            data-editor-contact-edit="${item.id}"
          >
            ${escapeHtml(tr('Edit'))}
          </button>

          <button
            type="button"
            class="btn danger subtle"
            data-editor-contact-remove="${item.id}"
          >
            ${escapeHtml(tr('Remove'))}
          </button>
        </div>
      </div>
    `;
  }

  function editorNoteMarkup(item) {
    return `
      <div
        class="job-tracking-row"
        data-inline-note-row="${item.id}"
      >
        <div class="job-tracking-row-main">
          <small>
            ${escapeHtml(
              fmtDateTime(
                item.created_at
              )
            )}
          </small>

          <div class="tracking-note-text">
            ${escapeHtml(
              item.note_text || ''
            )}
          </div>

          ${
            item.updated_at &&
            item.updated_at !==
              item.created_at
              ? `<span class="tracking-edited">${escapeHtml(tr('Edited'))}</span>`
              : ''
          }
        </div>

        <div class="job-tracking-row-actions">
          <button
            type="button"
            class="btn secondary"
            data-editor-note-edit="${item.id}"
          >
            ${escapeHtml(tr('Edit'))}
          </button>

          <button
            type="button"
            class="btn danger subtle"
            data-editor-note-remove="${item.id}"
          >
            ${escapeHtml(tr('Remove'))}
          </button>
        </div>
      </div>
    `;
  }

  function editorAttachmentMarkup(item) {
    return `
      <div
        class="job-tracking-row"
        data-inline-attachment-row="${item.id}"
      >
        <div class="job-tracking-row-main">
          <strong>
            ${escapeHtml(
              item.file_name ||
              tr('Attachment')
            )}
          </strong>

          <div class="tracking-meta">
            <span>
              ${escapeHtml(
                item.category ||
                tr('Other')
              )}
            </span>

            <span>
              ${escapeHtml(
                fmtDateTime(
                  item.created_at
                )
              )}
            </span>

            ${
              item.exists
                ? ''
                : `<span class="tracking-missing">${escapeHtml(tr('File missing'))}</span>`
            }
          </div>
        </div>

        <div class="job-tracking-row-actions">
          <button
            type="button"
            class="btn secondary"
            data-editor-attachment-open="${item.id}"
            ${item.exists ? '' : 'disabled'}
          >
            ${escapeHtml(tr('Open'))}
          </button>

          <button
            type="button"
            class="btn secondary"
            data-editor-attachment-folder="${item.id}"
            ${item.exists ? '' : 'disabled'}
          >
            ${escapeHtml(tr('Folder'))}
          </button>

          <button
            type="button"
            class="btn danger subtle"
            data-editor-attachment-remove="${item.id}"
          >
            ${escapeHtml(tr('Remove'))}
          </button>
        </div>
      </div>
    `;
  }

  function inlineContactEditorMarkup(contact = null) {
    return `
      <div
        class="job-tracking-inline-editor"
        data-inline-contact-editor
        data-contact-id="${contact?.id || ''}"
      >
        <div class="tracking-form-grid">
          <label>
            ${escapeHtml(tr('Name'))}
            <input
              class="control full"
              data-editor-contact-name
              value="${escapeHtml(contact?.name || '')}"
            >
          </label>

          <label>
            ${escapeHtml(tr('Role'))}
            <input
              class="control full"
              data-editor-contact-role
              value="${escapeHtml(contact?.role || '')}"
              placeholder="Recruiter, Hiring Manager..."
            >
          </label>

          <label>
            ${escapeHtml(tr('Email'))}
            <input
              class="control full"
              type="email"
              data-editor-contact-email
              value="${escapeHtml(contact?.email || '')}"
            >
          </label>

          <label>
            ${escapeHtml(tr('Phone'))}
            <input
              class="control full"
              data-editor-contact-phone
              value="${escapeHtml(contact?.phone || '')}"
            >
          </label>

          <label class="tracking-span-2">
            ${escapeHtml(tr('Link'))}
            <input
              class="control full"
              data-editor-contact-url
              value="${escapeHtml(contact?.url || '')}"
              placeholder="https://..."
            >
          </label>

          <label class="tracking-span-2">
            ${escapeHtml(tr('Note'))}
            <textarea
              class="control full"
              data-editor-contact-note
            >${escapeHtml(contact?.note || '')}</textarea>
          </label>
        </div>

        <div class="job-tracking-inline-actions">
          <button
            type="button"
            class="btn secondary"
            data-editor-contact-cancel
          >
            ${escapeHtml(tr('Cancel'))}
          </button>

          <button
            type="button"
            class="btn gold"
            data-editor-contact-save
          >
            ${escapeHtml(tr('Save'))}
          </button>
        </div>
      </div>
    `;
  }

  function inlineNoteEditorMarkup(note = null) {
    return `
      <div
        class="job-tracking-inline-editor"
        data-inline-note-editor
        data-note-id="${note?.id || ''}"
      >
        <label>
          ${escapeHtml(tr('Note'))}

          <textarea
            class="control full tracking-note-editor"
            data-editor-note-text
          >${escapeHtml(note?.note_text || '')}</textarea>
        </label>

        <div class="job-tracking-inline-actions">
          <button
            type="button"
            class="btn secondary"
            data-editor-note-cancel
          >
            ${escapeHtml(tr('Cancel'))}
          </button>

          <button
            type="button"
            class="btn gold"
            data-editor-note-save
          >
            ${escapeHtml(tr('Save'))}
          </button>
        </div>
      </div>
    `;
  }

  function showInlineContactEditor(
    host,
    applicationId,
    contact = null
  ) {
    const slot =
      $('[data-editor-contact-editor-slot]', host);

    if (!slot) {
      return;
    }

    slot.innerHTML =
      inlineContactEditorMarkup(
        contact
      );

    const editor =
      $('[data-inline-contact-editor]', slot);

    $('[data-editor-contact-cancel]', editor)
      .onclick =
      () => {
        slot.innerHTML = '';
      };

    $('[data-editor-contact-save]', editor)
      .onclick =
      async () => {
        const payload = {
          name:
            $('[data-editor-contact-name]', editor)
              .value
              .trim(),

          role:
            $('[data-editor-contact-role]', editor)
              .value
              .trim(),

          email:
            $('[data-editor-contact-email]', editor)
              .value
              .trim(),

          phone:
            $('[data-editor-contact-phone]', editor)
              .value
              .trim(),

          url:
            $('[data-editor-contact-url]', editor)
              .value
              .trim(),

          note:
            $('[data-editor-contact-note]', editor)
              .value
              .trim()
        };

        try {
          if (contact?.id) {
            await api(
              'update_application_contact',
              Number(contact.id),
              payload
            );
          } else {
            await api(
              'add_application_contact',
              Number(applicationId),
              payload
            );
          }

          await renderInlineTracking(
            applicationId,
            host
          );

          toast(
            contact?.id
              ? tr('Contact updated.')
              : tr('Contact added.'),
            'success'
          );
        } catch (error) {
          toast(
            error.message,
            'error'
          );
        }
      };
  }

  function showInlineNoteEditor(
    host,
    applicationId,
    note = null
  ) {
    const slot =
      $('[data-editor-note-editor-slot]', host);

    if (!slot) {
      return;
    }

    slot.innerHTML =
      inlineNoteEditorMarkup(
        note
      );

    const editor =
      $('[data-inline-note-editor]', slot);

    $('[data-editor-note-cancel]', editor)
      .onclick =
      () => {
        slot.innerHTML = '';
      };

    $('[data-editor-note-save]', editor)
      .onclick =
      async () => {
        const value =
          $('[data-editor-note-text]', editor)
            .value
            .trim();

        try {
          if (note?.id) {
            await api(
              'update_application_note',
              Number(applicationId),
              Number(note.id),
              value
            );
          } else {
            await api(
              'add_application_note',
              Number(applicationId),
              value
            );
          }

          await renderInlineTracking(
            applicationId,
            host
          );

          toast(
            note?.id
              ? tr('Note updated.')
              : tr('Note added.'),
            'success'
          );
        } catch (error) {
          toast(
            error.message,
            'error'
          );
        }
      };
  }

  async function renderInlineTracking(
    applicationId,
    host
  ) {
    if (
      !host ||
      !Number(applicationId)
    ) {
      return;
    }

    try {
      host.innerHTML = `
        <div class="job-tracking-loading">
          ${escapeHtml(tr('Loading tracking data...'))}
        </div>
      `;

      const result =
        await api(
          'get_application_tracking',
          Number(applicationId)
        );

      const tracking =
        result.tracking || {};

      const contacts =
        tracking.contacts || [];

      const notes =
        tracking.notes || [];

      const attachments =
        tracking.attachments || [];

      host.innerHTML = `
        <section class="job-tracking-section">
          <div class="job-tracking-section-head">
            <div>
              <span class="eyebrow">
                ${escapeHtml(tr('CONTACTS'))}
              </span>

              <strong>
                ${escapeHtml(tr('Contacts'))}
              </strong>
            </div>

            <button
              type="button"
              class="btn gold"
              data-editor-add-contact
            >
              + ${escapeHtml(tr('Add contact'))}
            </button>
          </div>

          <div data-editor-contact-editor-slot></div>

          <div class="job-tracking-list">
            ${
              contacts.length
                ? contacts
                    .map(editorContactMarkup)
                    .join('')
                : `<p class="muted">${escapeHtml(tr('No contacts yet.'))}</p>`
            }
          </div>
        </section>

        <section class="job-tracking-section">
          <div class="job-tracking-section-head">
            <div>
              <span class="eyebrow">
                ${escapeHtml(tr('NOTES HISTORY'))}
              </span>

              <strong>
                ${escapeHtml(tr('Notes history'))}
              </strong>
            </div>

            <button
              type="button"
              class="btn gold"
              data-editor-add-note
            >
              + ${escapeHtml(tr('Add note'))}
            </button>
          </div>

          <div data-editor-note-editor-slot></div>

          <div class="job-tracking-list">
            ${
              notes.length
                ? notes
                    .map(editorNoteMarkup)
                    .join('')
                : `<p class="muted">${escapeHtml(tr('No notes yet.'))}</p>`
            }
          </div>
        </section>

        <section class="job-tracking-section">
          <div class="job-tracking-section-head">
            <div>
              <span class="eyebrow">
                ${escapeHtml(tr('ATTACHMENTS'))}
              </span>

              <strong>
                ${escapeHtml(tr('Attachments'))}
              </strong>
            </div>

            <div class="job-tracking-attachment-tools">
              <select
                class="control"
                data-editor-attachment-category
              >
                <option value="CV">CV</option>
                <option value="Cover letter">${escapeHtml(tr('Cover letter'))}</option>
                <option value="Screenshot">${escapeHtml(tr('Screenshot'))}</option>
                <option value="Other">${escapeHtml(tr('Other'))}</option>
              </select>

              <button
                type="button"
                class="btn gold"
                data-editor-add-attachment
              >
                + ${escapeHtml(tr('Add file'))}
              </button>
            </div>
          </div>

          <p class="muted job-tracking-local-note">
            ${escapeHtml(
              tr(
                'Attachments are copied into JAM local storage.'
              )
            )}
          </p>

          <div class="job-tracking-list">
            ${
              attachments.length
                ? attachments
                    .map(editorAttachmentMarkup)
                    .join('')
                : `<p class="muted">${escapeHtml(tr('No attachments yet.'))}</p>`
            }
          </div>
        </section>
      `;

      $('[data-editor-add-contact]', host)
        .onclick =
        () => {
          showInlineContactEditor(
            host,
            applicationId
          );
        };

      $('[data-editor-add-note]', host)
        .onclick =
        () => {
          showInlineNoteEditor(
            host,
            applicationId
          );
        };

      $('[data-editor-add-attachment]', host)
        .onclick =
        async () => {
          const category =
            $('[data-editor-attachment-category]', host)
              ?.value ||
            'Other';

          try {
            const added =
              await api(
                'add_application_attachment',
                Number(applicationId),
                category
              );

            if (
              !added.cancelled
            ) {
              await renderInlineTracking(
                applicationId,
                host
              );

              toast(
                tr('Attachment added.'),
                'success'
              );
            }
          } catch (error) {
            toast(
              error.message,
              'error'
            );
          }
        };

      $$('[data-editor-contact-open]', host)
        .forEach(
          button => {
            button.onclick =
              async () => {
                const item =
                  contacts.find(
                    row =>
                      Number(row.id) ===
                      Number(
                        button.dataset.editorContactOpen
                      )
                  );

                if (item?.url) {
                  try {
                    await api(
                      'open_url',
                      item.url
                    );
                  } catch (error) {
                    toast(
                      error.message,
                      'error'
                    );
                  }
                }
              };
          }
        );

      $$('[data-editor-contact-edit]', host)
        .forEach(
          button => {
            button.onclick =
              () => {
                const item =
                  contacts.find(
                    row =>
                      Number(row.id) ===
                      Number(
                        button.dataset.editorContactEdit
                      )
                  );

                if (item) {
                  showInlineContactEditor(
                    host,
                    applicationId,
                    item
                  );
                }
              };
          }
        );

      $$('[data-editor-contact-remove]', host)
        .forEach(
          button => {
            button.onclick =
              async () => {
                try {
                  await api(
                    'delete_application_contact',
                    Number(applicationId),
                    Number(
                      button.dataset.editorContactRemove
                    )
                  );

                  await renderInlineTracking(
                    applicationId,
                    host
                  );
                } catch (error) {
                  toast(
                    error.message,
                    'error'
                  );
                }
              };
          }
        );

      $$('[data-editor-note-edit]', host)
        .forEach(
          button => {
            button.onclick =
              () => {
                const item =
                  notes.find(
                    row =>
                      Number(row.id) ===
                      Number(
                        button.dataset.editorNoteEdit
                      )
                  );

                if (item) {
                  showInlineNoteEditor(
                    host,
                    applicationId,
                    item
                  );
                }
              };
          }
        );

      $$('[data-editor-note-remove]', host)
        .forEach(
          button => {
            button.onclick =
              async () => {
                try {
                  await api(
                    'delete_application_note',
                    Number(applicationId),
                    Number(
                      button.dataset.editorNoteRemove
                    )
                  );

                  await renderInlineTracking(
                    applicationId,
                    host
                  );
                } catch (error) {
                  toast(
                    error.message,
                    'error'
                  );
                }
              };
          }
        );

      $$('[data-editor-attachment-open]', host)
        .forEach(
          button => {
            button.onclick =
              async () => {
                const item =
                  attachments.find(
                    row =>
                      Number(row.id) ===
                      Number(
                        button.dataset.editorAttachmentOpen
                      )
                  );

                if (item?.stored_path) {
                  try {
                    await api(
                      'open_path',
                      item.stored_path
                    );
                  } catch (error) {
                    toast(
                      error.message,
                      'error'
                    );
                  }
                }
              };
          }
        );

      $$('[data-editor-attachment-folder]', host)
        .forEach(
          button => {
            button.onclick =
              async () => {
                const item =
                  attachments.find(
                    row =>
                      Number(row.id) ===
                      Number(
                        button.dataset.editorAttachmentFolder
                      )
                  );

                if (item?.stored_path) {
                  try {
                    await api(
                      'open_parent_folder',
                      item.stored_path
                    );
                  } catch (error) {
                    toast(
                      error.message,
                      'error'
                    );
                  }
                }
              };
          }
        );

      $$('[data-editor-attachment-remove]', host)
        .forEach(
          button => {
            button.onclick =
              async () => {
                try {
                  await api(
                    'delete_application_attachment',
                    Number(applicationId),
                    Number(
                      button.dataset.editorAttachmentRemove
                    )
                  );

                  await renderInlineTracking(
                    applicationId,
                    host
                  );
                } catch (error) {
                  toast(
                    error.message,
                    'error'
                  );
                }
              };
          }
        );
    } catch (error) {
      host.innerHTML = `
        <div class="job-tracking-error">
          ${escapeHtml(error.message)}
        </div>
      `;
    }
  }

  function enhanceJobEditorTracking(
    app = null
  ) {
    const root =
      $('#modalRoot');

    const form =
      $('#jobForm', root);

    if (!form) {
      return;
    }

    layoutPrimaryContactFields(
      form
    );

    if (
      form.querySelector(
        '[data-job-tracking-editor]'
      )
    ) {
      return;
    }

    const description =
      form.querySelector(
        '[name="description"]'
      )?.closest(
        'label'
      );

    if (!description) {
      return;
    }

    const wrapper =
      document.createElement(
        'div'
      );

    wrapper.className =
      'job-tracking-editor job-editor-span-2';

    wrapper.dataset.jobTrackingEditor =
      '1';

    description.parentElement.insertBefore(
      wrapper,
      description
    );

    wrapper.innerHTML = `
      <div class="job-tracking-editor-head">
        <div>
          <span class="eyebrow">
            ${escapeHtml(tr('TRACKING & HISTORY'))}
          </span>

          <h3>
            ${escapeHtml(tr('Contacts, notes & attachments'))}
          </h3>

          <p class="muted">
            ${escapeHtml(
              tr(
                'Keep multiple contacts, note history and application files together.'
              )
            )}
          </p>
        </div>

        ${
          app?.id
            ? `<button type="button" class="btn secondary" data-open-full-tracking>${escapeHtml(tr('Open full tracking'))}</button>`
            : ''
        }
      </div>

      <div data-job-tracking-content>
        ${
          app?.id
            ? `<div class="job-tracking-loading">${escapeHtml(tr('Loading tracking data...'))}</div>`
            : `<div class="job-tracking-locked">${escapeHtml(
                tr(
                  'Save this application first, then reopen it to add multiple contacts, note history and attachments.'
                )
              )}</div>`
        }
      </div>
    `;

    if (app?.id) {
      const host =
        $('[data-job-tracking-content]', wrapper);

      renderInlineTracking(
        Number(app.id),
        host
      );

      $('[data-open-full-tracking]', wrapper)
        .onclick =
        () => {
          showTrackingDetails(
            Number(app.id)
          );
        };
    }
  }

  function wrapJobEditorTracking() {
    const original =
      window.openJobModal;

    if (
      typeof original !==
        'function' ||
      original.__batch3EditorWrapped
    ) {
      return;
    }

    const wrapped =
      function(app = null) {
        const result =
          original(app);

        enhanceJobEditorTracking(
          app
        );

        return result;
      };

    wrapped.__batch3EditorWrapped =
      true;

    window.openJobModal =
      wrapped;

    try {
      openJobModal =
        wrapped;
    } catch (_) {}
  }

  function injectCaptureSettings() {
    if ($('#batch3CaptureSettings')) return;

    const panel = document.createElement('article');
    panel.id = 'batch3CaptureSettings';
    panel.className = 'panel capture-settings-panel';
    panel.innerHTML = `
      <span class="eyebrow">${escapeHtml(tr('CAPTURE MODE'))}</span>
      <h2>${escapeHtml(tr('Position, size & shortcuts'))}</h2>
      <p class="muted">${escapeHtml(tr('Capture remembers its exact window position and size on this PC.'))}</p>
      <div class="capture-settings-grid">
        <label>${escapeHtml(tr('Default position'))}
          <select class="control full" data-capture-default>
            <option value="top-left">${escapeHtml(tr('Top left'))}</option>
            <option value="top-right">${escapeHtml(tr('Top right'))}</option>
            <option value="bottom-left">${escapeHtml(tr('Bottom left'))}</option>
            <option value="bottom-right">${escapeHtml(tr('Bottom right'))}</option>
          </select>
        </label>
        <label class="capture-memory-toggle">
          <input type="checkbox" data-capture-remember>
          <span>${escapeHtml(tr('Remember exact position and size'))}</span>
        </label>
      </div>
      <button class="btn secondary" type="button" data-reset-capture-geometry>${escapeHtml(tr('Reset saved position & size'))}</button>
      <div class="shortcut-grid">
        <span><kbd>Ctrl</kbd> + <kbd>N</kbd></span><strong>${escapeHtml(tr('Add job'))}</strong>
        <span><kbd>Ctrl</kbd> + <kbd>K</kbd></span><strong>${escapeHtml(tr('Search applications'))}</strong>
        <span><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>C</kbd></span><strong>${escapeHtml(tr('Open Capture Mode'))}</strong>
        <span><kbd>Ctrl</kbd> + <kbd>S</kbd></span><strong>${escapeHtml(tr('Save project'))}</strong>
        <span><kbd>Ctrl</kbd> + <kbd>Enter</kbd></span><strong>${escapeHtml(tr('Run Analyzer'))}</strong>
        <span><kbd>Esc</kbd></span><strong>${escapeHtml(tr('Close dialog'))}</strong>
      </div>
      <p class="muted shortcut-note">${escapeHtml(tr('Keyboard shortcuts work while JAM is focused.'))}</p>
    `;

    const right = $('#settingsRightColumn');
    const danger = $('#settingsPage .danger-panel');
    if (right) {
      if (danger?.parentElement === right) right.insertBefore(panel, danger);
      else right.appendChild(panel);
    } else {
      $('#settingsPage .settings-grid')?.appendChild(panel);
    }

    const corner = $('[data-capture-default]', panel);
    const remember = $('[data-capture-remember]', panel);
    corner.value = state.settings.capture_corner || 'top-right';
    remember.checked = String(state.settings.capture_remember_geometry ?? '1') !== '0';

    corner.onchange = async () => {
      try {
        await saveSetting('capture_corner', corner.value);
        toast(tr('Default Capture position saved.'), 'success');
      } catch (error) { toast(error.message, 'error'); }
    };
    remember.onchange = async () => {
      try {
        await saveSetting('capture_remember_geometry', remember.checked ? '1' : '0');
        toast(tr('Capture preference saved.'), 'success');
      } catch (error) { toast(error.message, 'error'); }
    };
    $('[data-reset-capture-geometry]', panel).onclick = async () => {
      try {
        await api('clear_capture_geometry');
        toast(tr('Saved Capture position and size cleared.'), 'success');
      } catch (error) { toast(error.message, 'error'); }
    };
  }

  function installKeyboardShortcuts() {
    if (document.body.dataset.batch3Shortcuts === '1') return;
    document.body.dataset.batch3Shortcuts = '1';

    document.addEventListener('keydown', async event => {
      const key = event.key.toLowerCase();

      if (event.key === 'Escape' && $('#modalRoot')?.children.length) {
        closeModal();
        return;
      }

      if (!(event.ctrlKey || event.metaKey)) return;

      if (key === 'n' && !event.shiftKey && !event.altKey) {
        event.preventDefault();
        openJobModal();
        return;
      }

      if (key === 'k' && !event.shiftKey && !event.altKey) {
        event.preventDefault();
        navigate('applications');
        window.setTimeout(() => $('#searchInput')?.focus(), 40);
        return;
      }

      if (key === 'c' && event.shiftKey && !event.altKey) {
        event.preventDefault();
        $('#captureBtn')?.click();
        return;
      }

      if (key === 's' && !event.shiftKey && !event.altKey) {
        event.preventDefault();
        try {
          const status = await api('project_state');
          if (status.project_state?.current_path) {
            await api('save_current_project');
            toast(tr('Project saved.'), 'success');
          } else {
            await saveProject();
          }
        } catch (error) { toast(error.message, 'error'); }
        return;
      }

      if (event.key === 'Enter' && !event.shiftKey && !event.altKey) {
        const analyzerActive = $('#analyzerPage')?.classList.contains('active');
        if (analyzerActive) {
          event.preventDefault();
          $('#runAnalyzerBtn')?.click();
        }
      }
    });
  }

  async function init() {
    if (initialized) return;
    initialized = true;
    injectTrackingButton();
    wrapSelectionUi();
    syncTrackingSelection();
    wrapJobEditorTracking();
    installKeyboardShortcuts();

    // settings_polish creates the two settings columns after startup.
    window.setTimeout(injectCaptureSettings, 180);
    window.setTimeout(injectCaptureSettings, 600);
  }

  window.JAM_BATCH3 = {
    showTrackingDetails
  };

  document.addEventListener('pywebviewready', init);
  window.setTimeout(() => {
    if (!initialized && window.pywebview?.api) init();
  }, 120);
})();

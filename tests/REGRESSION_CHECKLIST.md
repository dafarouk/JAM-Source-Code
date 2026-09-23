# JAM Batch 1 Windows Regression Checklist

Run this checklist on the real Windows build after `pytest -q` passes.

## Startup / shutdown
- [ ] Launch JAM: one splash only, then the maximized main window.
- [ ] Close JAM with no active dirty `.jam`: closes normally.
- [ ] Open/save a `.jam`, change an application, then close JAM: Save / Don't Save / Cancel protection appears.
- [ ] Cancel the close: JAM stays open and usable.

## Language
- [ ] Settings → English / Français switches immediately.
- [ ] Switch EN → FR → EN without restarting: no labels remain stuck in the wrong language.
- [ ] Check Dashboard, Applications, filters, Add Job, Pipeline, Analyzer, Exports, Settings, Support, Logs, backup/diagnostics dialogs.
- [ ] Open Capture Mode in French: labels/statuses/analyzer messages are French.
- [ ] Create Excel + PDF in French: report title, filters, headers, statuses and dates are French.

## Applications
- [ ] Add Job → type data, close the app unexpectedly, relaunch: recovery prompt restores the draft.
- [ ] Save a job with tracking parameters in the URL: saved URL is clean/canonical.
- [ ] Change Saved → Applied: `date_applied` is set automatically once.
- [ ] Change Applied → Interviewing → Saved: original `date_applied` remains unchanged.
- [ ] Archive a job: hidden from normal Applications list by default.
- [ ] Search for an archived job: it appears in search results.
- [ ] Toggle Show archived: archived rows appear/disappear.
- [ ] Existing Excel-style column filters and sorting still work.
- [ ] Delete one and bulk-delete still ask for confirmation and work.

## Capture Mode
- [ ] Main window minimizes; Capture Mode opens pinned; close/Return restores main window.
- [ ] Mouse wheel remains smooth before/after analyzer use.
- [ ] Type an unsaved Capture job, close Capture, reopen: draft is restored.
- [ ] Save from Capture: draft clears and application appears in the main app.
- [ ] If a `.jam` is active, saving from Capture marks the project dirty after returning.

## Projects
- [ ] Save `.jam`, edit data, then try Open `.jam`: Save & continue / Continue without saving / Cancel works.
- [ ] Same protection works for Recent Project, Reset and Backup Restore.
- [ ] Force-close/crash after changing an active `.jam`, relaunch: Project Recovery prompt appears.
- [ ] Restore recovered project changes and save them successfully.

## Backups
- [ ] Create Backup creates a timestamped backup.
- [ ] Restore Backup lists backups with dates/sizes.
- [ ] Restore asks for confirmation.
- [ ] Restore automatically creates a `before_restore` safety backup first.
- [ ] After restore, applications/settings refresh correctly.

## Currency flags
- [ ] Disconnect internet and open Settings.
- [ ] Currency flags still display from `assets/flags`.
- [ ] Search TND/Tunisia/Tunisie and other supported currencies.

## Data locations / diagnostics
- [ ] Data Locations shows database, backups, exports, projects, logs and recovery paths.
- [ ] Every Open button opens the correct folder.
- [ ] Run Diagnostics: database/folders/flags/CV/WebView2/Python checks render clearly.
- [ ] Copy diagnostics copies readable text.

## Export regression
- [ ] New Excel opens without an Excel repair warning.
- [ ] Excel title/filter rows are centered and dates are readable.
- [ ] PDF opens normally.
- [ ] Export completion dialog Open file / Open folder works.

## Final smoke
- [ ] Support, Contact, About, Logs and Guide navigation still open.
- [ ] Pipeline drag/delete still works.
- [ ] Analyzer still runs from both Add Job and Capture Mode.
- [ ] No Python console traceback after normal use.

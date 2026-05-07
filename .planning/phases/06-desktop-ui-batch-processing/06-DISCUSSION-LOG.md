# Phase 6: Desktop UI & Batch Processing - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-07
**Phase:** 6 — Desktop UI & Batch Processing
**Areas discussed:** UI framework, Output directory, File list UX, Error display

---

## UI Framework

### Question 1: Which UI framework?

| Option | Description | Selected |
|--------|-------------|----------|
| tkinter | Ships with Python 3.11 stdlib — zero extra install for billing staff | ✓ |
| PyQt5 | Richer native-looking widgets, better styling control; requires extra pip install | |

**User's choice:** tkinter
**Notes:** Consistent with existing PROJECT.md "pending" decision — tkinter is sufficient for this scope.

### Question 2: Startup dependency check behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Block on startup | Run setup_check before window opens; messagebox error + exit if deps missing | ✓ |
| Show window, then check | Open window immediately; disable Start button if deps missing | |

**User's choice:** Block on startup

### Question 3: Window resizability

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed size | ~500×400px, no reflow needed | ✓ |
| Resizable | Allows expanding to see more of the file list | |

**User's choice:** Fixed size

---

## Output Directory

### Question 1: How does the user control output location?

| Option | Description | Selected |
|--------|-------------|----------|
| Always use settings['output_dir'] | Silent write to configured dir (Desktop default); no per-run picker | ✓ |
| Folder picker in the UI | A 'Save to...' button lets users pick per-run | |

**User's choice:** Always use settings['output_dir']
**Notes:** Resolves the open decision flagged in STATE.md: "Output filename/directory convention — confirm before Phase 6 UI build."

### Question 2: Show output path in UI?

| Option | Description | Selected |
|--------|-------------|----------|
| Show path as a label | Read-only label displaying full path before/during/after run | ✓ |
| No — just open it | No path shown; 'Open output file' button handles it | |

**User's choice:** Show path as a label

---

## File List UX

### Question 1: Show files in list before starting?

| Option | Description | Selected |
|--------|-------------|----------|
| Show file list, then Start | Listbox shows filenames; user reviews, then clicks Start | ✓ |
| Pick and go | Clicking 'Select PDFs' immediately triggers processing | |

**User's choice:** Show file list, then Start

### Question 2: Cancel during processing?

| Option | Description | Selected |
|--------|-------------|----------|
| No cancel — disable UI controls | Disable buttons during run; progress bar + error log still update | ✓ |
| Cancel button | Graceful stop via event flag; writes completed rows | |

**User's choice:** No cancel — disable UI controls

### Question 3: Can user start another run?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — reset and reuse the window | Re-enable controls, clear list after completion; window reusable | ✓ |
| One run per session | Window stays in 'done' state; reopen app for next batch | |

**User's choice:** Yes — reset and reuse the window

---

## Error Display

### Question 1: How to show post-run error summary?

| Option | Description | Selected |
|--------|-------------|----------|
| Inline status label | Simple label below progress bar with count and brief list | |
| Pop-up messagebox | tkinter messagebox after completion; user must dismiss | |
| Scrollable error log | Scrollable Text widget in window; accumulates errors during run | ✓ |

**User's choice:** Scrollable error log

### Question 2: Always visible or appears on first error?

| Option | Description | Selected |
|--------|-------------|----------|
| Always visible | Text widget in fixed layout from startup; empty at idle | ✓ |
| Appear on first error | Hidden at startup; shown when first error occurs | |

**User's choice:** Always visible

### Question 3: Error line format?

| Option | Description | Selected |
|--------|-------------|----------|
| File + page + error message | `{filename} page {N}: {error_message}` — full context | ✓ |
| Page number + error type only | `Page 4: conversion error` — compact but ambiguous in multi-file batches | |

**User's choice:** File + page + error message

---

## Claude's Discretion

- Widget layout order within the fixed window (top-to-bottom vs grouped arrangement)
- ttk vs plain tk per widget (use ttk where it gives better Windows native look)
- `mkdir -p output_dir` before `write_workbook()` — silently create if missing (fixes WR-02)
- Page counter strategy: `("progress", current, total)` tuples via queue

## Deferred Ideas

None — discussion stayed within phase scope.

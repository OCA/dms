This module adds a side-by-side preview pane to the DMS file **list** and **kanban** views.

Clicking a row opens a slide-in pane that previews the file (images, PDF,
video/audio, code, markdown, e-mail, …) and exposes Download / Share / Open
actions plus a Details tab and an Activity tab with the file's chatter. The
pane is toggleable (persisted per browser) and the chatter is collapsible.

It is implemented as a pure extension of the ``dms`` list + kanban renderers (no changes
to the ``dms`` module itself), so it can be installed or removed independently.

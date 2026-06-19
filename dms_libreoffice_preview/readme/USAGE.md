No configuration required. With LibreOffice on the server and this
module installed, opening any office file (`.doc{x}`, `.odt`, `.xls{x}`,
`.ods`, `.ppt{x}`, `.odp`, `.rtf`) from the DMS kanban or list view
shows the rendered PDF in the side-pane preview.

The first open takes 1–5 seconds (LibreOffice conversion); subsequent
opens hit the cached attachment and feel instant. If the source file
changes (new content, new name, etc.), the cache invalidates and the
next open triggers a fresh conversion.

If LibreOffice fails to convert a file (corrupt source, unusual format
variation), the side-pane shows a brief error message. The original
file is always downloadable via the side-pane toolbar's Download button
regardless of preview success.

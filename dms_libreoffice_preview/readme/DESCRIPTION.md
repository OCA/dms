Adds in-browser preview of office file formats (Word, Excel, PowerPoint,
OpenDocument, RTF) to OCA DMS by converting them to PDF on the server
with a headless LibreOffice subprocess. The converted PDF is cached as
a child `ir.attachment` of the source `dms.file` and served via the
existing side-pane preview registry (`dms.preview_handlers`), so the
browser's native PDF viewer renders the result with no new UI code.

Without this module, office files in DMS fall back to a download-only
card. Install this module on any deployment where LibreOffice can be
installed system-wide and you don't need full in-browser editing (use
`dms_onlyoffice` for that).

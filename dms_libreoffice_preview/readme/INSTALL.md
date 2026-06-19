## System dependencies

LibreOffice must be installed on the Odoo server. On Debian / Ubuntu:

```
apt-get install libreoffice fonts-noto fonts-liberation
```

The `fonts-noto` and `fonts-liberation` packages are recommended even if
your container already has a font set — headless LibreOffice falls back
to ugly substitutes when common fonts are missing, which produces
unreadable PDFs for typical office documents.

Once LibreOffice is on the `PATH`, install this module as usual. The
preview is lazy: nothing converts until the first time a user opens an
office file in the DMS side-pane. Subsequent opens of the same file
(same `write_date`) hit the `ir.attachment` cache.

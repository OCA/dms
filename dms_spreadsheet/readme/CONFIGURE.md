No additional configuration is required after installing the module.

Spreadsheet files are identified by the MIME type `application/o-spreadsheet` and the
`handler` field value `spreadsheet` on `dms.file` records. Both are set automatically
when a file is created through the **New Spreadsheet** wizard or when an existing DMS
file's MIME type is set to `application/o-spreadsheet`.

Access to individual spreadsheets is governed by the existing DMS permission system
(storage-level groups and directory-level ACLs).

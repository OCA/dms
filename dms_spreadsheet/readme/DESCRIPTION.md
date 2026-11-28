Create and edit OCA spreadsheets directly within the DMS file manager.

Requires `dms` and `spreadsheet_oca`.

**Features**

- **New Spreadsheet** button in DMS directory views (form and kanban)
- Opening a `.o-spreadsheet` file launches the full OCA spreadsheet editor
- Spreadsheet data stored transparently via DMS file storage (database, attachment, or filesystem)
- Read-only mode for users without write access to the DMS file
- Revision history via `spreadsheet.abstract` mixin

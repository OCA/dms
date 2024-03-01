Documents Versioning enables version control for the document management system.

Configuration
~~~~~~~~~~~~~

* allow versioning on storage level (only for type "database" and "filestore" -> NOT "attachment" currently)
* allow versioning on directory level
* allow versioning on file level
* allow changing the versioning setting later only for people with special group + track change in chatter of dms file

DMS Files
~~~~~~~~~

* link the "origin" file when creating a new version
    * If a file is newly created, origin is self
    * If a version is created for a file, origin is copied (so that the entire history of a file knows which file was the origin)
* use active-boolean to mark newest version
    * There is only one active file for all files with the same origin (unique contraint).
    * Files with active = False are readonly to avoid creating new versions from archived files.
* link the "parent" file when creating a new version
    * If a file is newly created, parent is False.
    * If a version is created for a file, parent is the "old" file.
* count the number of versions for files with the same origin_id (unique contraint for version number and origin)
* only show files with active=True in tree and kanban views
* track changes of almost all fields of a file
* add a smartbutton in file form view to show all versions with the same orgin (attention: show archived files)
* add icon in kanban view if a file is not the origin (to mark a file as modified)
* color file in yellow in tree view that is not the origin (to mark a file as modified)
* add a filter to show all modified files (parent != False)
* add a filter to show all not-modified files (parent = False)
* add a filter to show all archived files (active=False)
* do not allow to use the usual action "Unarchive" - instead use the restore button in archived files

Versioning
~~~~~~~~~~

* change the content field of a file to create a new version
    * do not allow to change the content if the file is active=False
    * The old file is the parent of the new file.
    * The old file is now active=False.
    * The new file is active=True.
    * A chatter message is created in the new file to know from which file it was created.
    * A chatter message is created in the parent file to know which file was generated from it.
    * A chatter message is created in the origin file (if origin != parent) to see the entire history of all versions in the origin file.

Restoring
~~~~~~~~~

* click a button in form or tree view to restore an archived file
    * The old archived file is now active=True.
    * If an active=True file existed with the same origin it now is active=False.
    * A chatter message is created in the previously archived and now restored file.
    * A chatter message is created in the previously active and now archived file (if one existed).
    * A chatter message is created in the origin file (if origin != restored file and origin != previous active file).

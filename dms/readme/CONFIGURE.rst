To configure this module, you need to:

#. Go to *Documents -> Configuration -> Storages*.
#. Create a new document storage. You can choose between two options on `Save Type`:
    * `Database`: Store the files on the database as a field
    * `Attachment`: Store the files as attachments
#. Afterwards go to *Documents -> Directories*.
#. Create a new directory, mark it as root and select the previously created setting.
#. On the Directory you can also define the access groups that will be able to:
    * read
    * create
    * write
    * delete


Migration
~~~~~~~~~

If you need to modify the storage Save Type you might want to migrate the file data.
In order to achieve it you need to:

#. Go to *Documents -> Configuration -> Storage* and select the storage you want to modify
#. Modify the save type
#. Press the button `Migrate files` if you want to migrate all the files at once
#. Press the button `Manual File Migration` in order to specify files one by one

You can check all the files that still needs to be migrated from all storages
and migrate them manually on *Documents -> Configuration -> Migration*

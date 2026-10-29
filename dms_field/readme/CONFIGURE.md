To use the embedded view in any module, the module must inherit from the
mixin dms.field.mixin (You have an example with res.partner in this
module).

Once this is done, in the form view of the model we will have to add the
following:

``` xml
<field name="dms_directory_ids" mode="dms_list" />
```

In addition, it will be necessary to create an Embedded DMS template for
this model.

1.  *Go to Documents \> Configuration \> Embedded DMS templates* and
    create a new record.
2.  Set a storage, a model (res.partner for example) and the access
    groups you want.
3.  You can also use expressions in "Directory format name", for
    example: {{object.name}}
4.  Click on the "Documents" tab icon and a folder hierarchy will be
    created.
5.  You can set here the hierarchy of directories, subdirectories and
    files you need, this hierarchy will be used as a base when creating
    a new record (res.partner for example).

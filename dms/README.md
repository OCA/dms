# MuK Document Management System

MuK Documents is a module to create, manage and view files within Odoo.

---

<img align="center" src="static/description/demo.gif"/>

## Place Documents into other models

### Model

```python
file = fields.Many2one('muk_dms.file', string='Document')
```

### Record (XML)

```xml
<field name="dmsfile" widget="dms_file" string="Datei" />
```

```xml
<field name="dmsfile" widget="dms_file" string="Datei" filename="field_filename" directory="ref_directory_id" />
```

```xml
<field name="dmsfile" widget="dms_file" string="Datei" downloadonly="downloadonly" />
```

## Requirements

* mammoth

```bash
$ sudo pip install mammoth
```
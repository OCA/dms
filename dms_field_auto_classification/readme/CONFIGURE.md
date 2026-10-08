1.  Go to Documents / Configuration / Classification Templates and
    create or edit a template.
2.  You can set a model to which it is linked (res.partner for example).
3.  You can define the details to indicate which field is referenced by
    the defined filename pattern.

Full example from res.partner:

Filename pattern: (\[0-9\]{8}\[A-Z\]).\*.pdf Details: VAT (field) and 0
(index) Directory Pattern example 1: {0} \> This will attempt to add the
files to the directory linked to the partner with the VAT name.
Directory Pattern example 2: {0} / Misc \> This will attempt to add the
files to the "Misc" subdirectory linked to the partner with the VAT
name.

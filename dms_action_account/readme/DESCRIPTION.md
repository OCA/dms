This module extends DMS actions to create customer invoices, vendor bills,
customer credit notes and vendor credit notes from DMS files.

The action creates a draft invoice using the configured partner and journal,
attaches the DMS file as the invoice's main attachment and opens the invoice form.

The created invoice is stored on the DMS action. Subsequent executions of the
same action open that invoice, including when executed from another DMS file.
No invoice lines are created automatically.

1. Install this module and its dependencies, DMS Actions and Accounting.
2. Open the DMS action configuration and create an action.
3. Select **Create Invoice** as the action kind.
4. Choose the invoice type: customer invoice, vendor bill, customer credit note
   or vendor credit note.
5. Select a sales journal for customer documents or a purchase journal for vendor
   documents, using the same company as the invoice.
6. Select the partner to use on the invoice.
7. Select the directories where the action should be available and, optionally,
   restrict access using the allowed groups.

Execute the action from a file in an eligible directory to create and open the
invoice. The **Invoice** field on the action shows the linked invoice and is
read-only. Further executions open the same invoice without creating another
invoice or attaching additional files.

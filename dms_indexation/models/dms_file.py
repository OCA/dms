import base64
import re
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
from odoo import models, fields, api

class DmsFile(models.Model):
    _inherit = "dms.file"

    index_content = fields.Text('Indexed Content', readonly=True, prefetch=False)

    @api.model
    def create(self, vals):
        if vals.get('content'):
            binary_data = base64.b64decode(vals['content'])
            vals['index_content'] = self._index(binary_data, vals.get('mimetype'))
        return super(DmsFile, self).create(vals)

    def write(self, vals):
        if 'content' in vals:
            binary_data = base64.b64decode(vals['content'])
            vals['index_content'] = self._index(binary_data, vals.get('mimetype'))
        return super(DmsFile, self).write(vals)

    @api.model
    def _index(self, bin_data, file_type):
        """ Compute the index content of the given binary data.
            This extends Odoo's indexing logic for multiple file formats.
        """
        index_content = False

        if file_type:
            if file_type.startswith('text/'):
                words = re.findall(b"[\x20-\x7E]{4,}", bin_data)
                index_content = b"\n".join(words).decode('ascii')

            elif file_type == 'application/pdf':
                try:
                    pdf_reader = PdfReader(BytesIO(bin_data))
                    text_content = '\n'.join(page.extract_text() or "" for page in pdf_reader.pages)
                    if not text_content.strip():
                        images = convert_from_bytes(bin_data, dpi=300)
                        text_content = "\n".join(pytesseract.image_to_string(img) for img in images)
                    index_content = text_content
                except Exception:
                    index_content = ''

            elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                try:
                    doc = Document(BytesIO(bin_data))
                    index_content = '\n'.join(p.text for p in doc.paragraphs)
                except Exception:
                    index_content = ''

            elif file_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                try:
                    df = pd.read_excel(BytesIO(bin_data))
                    index_content = '\n'.join(
                        f'Row {i + 1}: {" | ".join(f"{col}: {row[col]}" for col in df.columns)}'
                        for i, row in df.iterrows()
                    )
                except Exception:
                    index_content = ''

            elif file_type in ['image/png', 'image/jpeg', 'image/jpg', 'image/svg']:
                try:
                    image = Image.open(BytesIO(bin_data))
                    index_content = pytesseract.image_to_string(image)
                except Exception:
                    index_content = ''

        return index_content

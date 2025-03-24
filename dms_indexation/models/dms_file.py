from odoo import api, fields, models, tools
from pdf2image import convert_from_bytes
import base64
from io import BytesIO
from pypdf import PdfReader
import pytesseract
import re
import pandas as pd
from PIL import Image
from docx import Document


class DMSFile(models.Model):
    _inherit = "dms.file"
    _description = "File"

    index_content = fields.Text(
        string="Indexed Content",
        compute="_compute_index_content",
        store=True
    )

    @api.depends('content', 'mimetype')
    def _compute_index_content(self):
        for record in self:
            binary = base64.b64decode(record.content or "")
            text_content = ''

            if record.mimetype == 'application/pdf':
                try:
                    pdf_reader = PdfReader(BytesIO(binary))
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        page_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', page_text)
                        text_content += page_text
                    if not text_content:
                        images = convert_from_bytes(binary, dpi=300)
                        extracted_text = [pytesseract.image_to_string(img) for img in images]
                        text_content = "\n".join(extracted_text)
                except:
                    text_content = ''

            elif record.mimetype == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                try:
                    doc = Document(BytesIO(binary))
                    text_content = '\n'.join([p.text for p in doc.paragraphs])
                except:
                    text_content = ''

            elif record.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                try:
                    df = pd.read_excel(BytesIO(binary))
                    text_content = '\n'.join([f'Row {i + 1}: {" ".join(f"{col}: {row[col]}" for col in df.columns)}'
                                              for i, row in df.iterrows()])
                except:
                    text_content = ''

            elif record.mimetype in ['image/png', 'image/jpeg', 'image/jpg', 'image/svg']:
                try:
                    image = Image.open(BytesIO(binary))
                    text_content = pytesseract.image_to_string(image)
                except:
                    text_content = ''

            record.index_content = text_content

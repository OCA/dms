{
    "name": "Avatax Exemptions with OCA Document extension",
    "version": "16.0.1.0.0",
    "category": "Sales",
    "summary": """
        This application allows you to add Avatax exemptions with OCA dms module
    """,
    "website": "https://github.com/OCA/dms",
    "author": "Kencove,Sodexis, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "account_avatax_oca",
        "account_avatax_sale_oca",
        "account_avatax_exemption_base",
        "dms",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/dms_exemption_data.xml",
        "data/dms_workflow_rule_data.xml",
        "views/dms_views.xml",
        "views/exemption_views.xml",
    ],
    "demo": [
        "demo/directory.xml",
    ],
    "installable": True,
    "application": False,
}

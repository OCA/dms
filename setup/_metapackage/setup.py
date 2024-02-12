import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-dms",
    description="Meta package for oca-dms Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-dms>=15.0dev,<15.1dev',
        'odoo-addon-dms_attachment_link>=15.0dev,<15.1dev',
        'odoo-addon-dms_auto_classification>=15.0dev,<15.1dev',
        'odoo-addon-dms_field>=15.0dev,<15.1dev',
        'odoo-addon-dms_field_auto_classification>=15.0dev,<15.1dev',
        'odoo-addon-hr_dms_field>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)

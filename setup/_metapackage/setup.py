import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-dms",
    description="Meta package for oca-dms Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-dms>=16.0dev,<16.1dev',
        'odoo-addon-dms_auto_classification>=16.0dev,<16.1dev',
        'odoo-addon-dms_storage>=16.0dev,<16.1dev',
        'odoo-addon-dms_user_role>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)

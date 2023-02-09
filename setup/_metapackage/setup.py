import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-dms",
    description="Meta package for oca-dms Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-dms',
        'odoo13-addon-dms_attachment_link',
        'odoo13-addon-dms_field',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)

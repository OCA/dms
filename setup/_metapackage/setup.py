import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-dms",
    description="Meta package for oca-dms Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-dms',
        'odoo12-addon-dms_field',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)

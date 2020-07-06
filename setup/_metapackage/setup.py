import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-dms",
    description="Meta package for oca-dms Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-dms',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)

from setuptools import find_packages, setup

setup(
    # Description.
    name             = 'csv_drop_addon',
    version          = '1.0',
    author           = 'Enthought, Inc',
    author_email     = 'info@enthought.com',
    description      = \
        "Allows for Canopy to open CSV files with the Enaml UI Builder",

    package_data={
        'csv_drop_addon': ['ui/*.enaml']
    },

    # Requirements.
    install_requires = ['canopyapp_addon'],

    # # Plugins.
    entry_points = {
        'envisage.plugins': [
            'csv_drop = csv_drop_addon.csv_drop_plugin:CSVDropPlugin',
        ]
    },

    zip_safe = False,

    # Packaging.
    packages         = find_packages(),
)

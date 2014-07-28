from setuptools import find_packages, setup

setup(
    # Description.
    name             = 'import_addon',
    version          = '1.0',
    author           = 'Enthought, Inc',
    author_email     = 'info@enthought.com',
    description      = \
        "Allows for Canopy to open data files with Canopy.",

    package_data={
        'import_addon': [
            'ui/*.enaml'
        ]
    },

    # Requirements.
    install_requires = ['canopyapp_addon'],

    # # Plugins.
    entry_points = {
        'envisage.plugins': [
            'import_addon = import_addon.plugin:ImportPlugin',
        ]
    },

    zip_safe = False,

    # Packaging.
    packages         = find_packages(),
)

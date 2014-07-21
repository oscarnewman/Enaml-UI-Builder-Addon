from setuptools import find_packages, setup

setup(
    # Description.
    name             = 'ui_builder_addon',
    version          = '1.0',
    author           = 'Enthought, Inc',
    author_email     = 'info@enthought.com',
    description      = \
        "Allows for Canopy to open CSV files with the Enaml UI Builder",

    package_data={
        'ui_builder_addon': [
            'ui/*.enaml',
            'img/*.png'
        ]
    },

    # Requirements.
    install_requires = ['canopyapp_addon'],

    # # Plugins.
    entry_points = {
        'envisage.plugins': [
            'builder_addon = ui_builder_addon.plugin:UIBuilderPlugin',
        ]
    },

    zip_safe = False,

    # Packaging.
    packages         = find_packages(),
)

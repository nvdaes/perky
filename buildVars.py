
# Build customizations
# Change this file instead of sconstruct or manifest files, whenever possible.

from site_scons.site_tools.NVDATool.typings import AddonInfo, BrailleTables, SymbolDictionaries

# Since some strings in `addon_info` are translatable,
# we need to include them in the .po files.
# Gettext recognizes only strings given as parameters to the `_` function.
# To avoid initializing translations in this module we simply import a "fake" `_` function
# which returns whatever is given to it as an argument.
from site_scons.site_tools.NVDATool.utils import _


# Add-on information variables
addon_info = {
    # for previously unpublished addons, please follow the community guidelines at:
    # https://bitbucket.org/nvdaaddonteam/todo/raw/master/guideLines.txt
    # add-on Name, internal for nvda
    "addon_name": "perky",
    # Add-on summary, usually the user visible name of the addon.
    # Translators: Summary for this add-on to be shown on installation and add-on information.
    "addon_summary": _("Perky Duck"),
    # Add-on description
    # Translators: Long description to be shown for this add-on on add-on information from add-ons manager
    "addon_description": _("""Improves the reading experiencewith Perky Duck.\n\tPerky Duck can be found at\n\thttps://www.duxburysystems.com\n\t"""),
    # version
    "addon_version": "10.0.0",
    # Brief changelog for this version
    # Translators: what's new content for the add-on version to be shown in the add-on store
    "addon_changelog": _("* Compatible with NVDA 2026.1."),
    # Author(s)
    "addon_author": u"Alejandro Iván Castro Orozco <alivcaor@gmail.com>, Noelia Ruiz Martínez <nrm1977@gmail.com>, Abdel <abdelkrim.bensaid@gmail.com>",
    # URL for the add-on documentation support
    "addon_url": "https://github.com/nvdaes/perky",
    # Documentation file name
    "addon_docFileName": "readme.html",
    # Minimum NVDA version supported (e.g. "2018.3")
    "addon_minimumNVDAVersion": "2026.1",
    # Last NVDA version supported/tested (e.g. "2018.4", ideally more recent than minimum version)
    "addon_lastTestedNVDAVersion": "2026.1",
    # Add-on update channel (default is stable or None)
    "addon_updateChannel": None,
}

# Define the python files that are the sources of your add-on.
# You can use glob expressions here, they will be expanded.
pythonSources = ["addon/appModules/*.py"]

# Files that contain strings for translation. Usually your python sources
i18nSources = pythonSources + ["buildVars.py"]

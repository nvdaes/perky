# -*- coding: UTF-8 -*-

# installTasks for perky, based on the readFeeds add-on
# Copyright (C) 2024 Noelia Ruiz Martínez, other contributors
# Released under GPL2

import os
import shutil
import glob

import addonHandler
import globalVars

ADDON_DIR = os.path.abspath(os.path.dirname(__file__))
SYMBOLS_PATH = os.path.join(ADDON_DIR, "appModules", "symbols")
CONFIG_PATH = globalVars.appArgs.configPath

addonHandler.initTranslation()


def onInstall():
	previousSymbolsPath = os.path.join(
		CONFIG_PATH, "addons", "perky",
		"appModules", "symbols"
	)
	if os.path.isdir(previousSymbolsPath):
		validFiles = glob.glob(previousSymbolsPath + "\\*.dic")
		if not os.path.isdir(SYMBOLS_PATH):
			os.makedirs(SYMBOLS_PATH)
		for file in validFiles:
			try:
				shutil.copy(file, SYMBOLS_PATH)
			except IOError:
				pass

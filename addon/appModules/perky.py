# -*- coding: UTF-8 -*-
# perky: app module for Perky Duck
# https://www.duxburysystems.com
# Copyright (C) 2024 Noelia Ruiz Martínez, other contributors
# Released under GPL 2

import os
import wx

import addonHandler
import appModuleHandler
import globalVars
import characterProcessing
import languageHandler
import api
import config
import textInfos
from scriptHandler import script
import speech
import ui
from NVDAObjects.window import DisplayModelEditableText
from NVDAObjects.behaviors import EditableTextWithAutoSelectDetection, KeyboardHandlerBasedTypedCharSupport
from NVDAObjects.IAccessible import IAccessible, ContentGenericClient
import controlTypes
import gui
from gui import guiHelper
from gui.settingsDialogs import SpeechSymbolsDialog

SYMBOLS_DIR = "symbols"

pathToDict = None

addonHandler.initTranslation()


def disableInSecureMode(decoratedCls):
	if globalVars.appArgs.secure:
		return appModuleHandler.AppModule
	return decoratedCls


class SymbolProcessor:

	def __init__(self, pathToDict=None):
		characterProcessing.clearSpeechSymbols()
		try:
			symbolProcessor = characterProcessing._localeSpeechSymbolProcessors.fetchLocaleData(
				speech.getCurrentLanguage()
			)
		except LookupError:
			symbolProcessor = characterProcessing._localeSpeechSymbolProcessors.fetchLocaleData("en")
		if pathToDict is None:
			pathToDict = os.path.join(
				os.path.dirname(__file__), SYMBOLS_DIR, os.path.basename(symbolProcessor.userSymbols.fileName)
			)
		self.pathToDict = pathToDict
		try:
			symbolProcessor.userSymbols.load(pathToDict)
		except Exception:
			pass
		characterProcessing._localeSpeechSymbolProcessors.invalidateLocaleData(symbolProcessor.locale)
		self.locale = symbolProcessor.locale


class PerkySpeechSymbolsDialog(SpeechSymbolsDialog):

	helpId = ""

	def __init__(self, parent):
		super().__init__(
			parent,
		)
		if pathToDict is not None:
			dictName = os.path.splitext(os.path.basename(pathToDict))[0]
		else:
			dictName = ""
		self.SetTitle(f"Perky {dictName} - {self.title}")

	def makeSettings(self, settingsSizer):
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		bHelper = guiHelper.ButtonHelper(orientation=wx.HORIZONTAL)
		bHelper.addButton(
			parent=self,
			# Translators: The label for a button in the Perky speech symbols dialog.
			label=_("&Save dictionary...")
		).Bind(wx.EVT_BUTTON, self.onSaveClick)
		bHelper.addButton(
			parent=self,
			# Translators: The label for a button in the Perky speech symbols dialog.
			label=_("&Choose dictionary...")
		).Bind(wx.EVT_BUTTON, self.onOpenClick)
		sHelper.addItem(bHelper)
		super().makeSettings(settingsSizer)

	def onSaveClick(self, evt):
		filename = wx.FileSelector(
			_("Save As"), default_filename="newSpeechSymbols.dic", default_path=os.path.join(os.path.dirname(__file__), SYMBOLS_DIR),
			flags=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT, parent=self
		)
		if not filename:
			return
		global pathToDict
		pathToDict = filename
		self.symbolProcessor.userSymbols.fileName = filename
		dictName = os.path.splitext(os.path.basename(pathToDict))[0]
		self.symbolsList.SetFocus()
		self.SetTitle(f"Perky {dictName} - {self.title}")

	def onOpenClick(self, evt):
		filename = wx.FileSelector(
			_("Select dictionary..."), default_path=os.path.join(os.path.dirname(__file__), SYMBOLS_DIR),
			flags=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, parent=self
		)
		if not filename:
			return
		global pathToDict
		pathToDict = filename
		super().onCancel(evt)


class EnhancedDocument(KeyboardHandlerBasedTypedCharSupport):

	role = controlTypes.Role.DOCUMENT
	scriptCategory = "Perky Duck"

	def getPriorCharacter(self):
		charInfo = self.makeTextInfo(textInfos.POSITION_CARET).copy()
		charInfo.move(textInfos.UNIT_CHARACTER, -1)
		charInfo.expand(textInfos.UNIT_CHARACTER)
		return charInfo

	def event_gainFocus(self):
		super().event_gainFocus()
		self._shouldReportChars = 0
		self.customProcessor = SymbolProcessor(pathToDict)

	def event_loseFocus(self):
		super().event_loseFocus()
		characterProcessing.clearSpeechSymbols()
		self.customProcessor = None

	def event_typedCharacter(self, ch):
		super().event_typedCharacter(ch)
		charsToSuppress = (u"\b", "\r", "\n")
		if config.conf["keyboard"]["speakTypedCharacters"] and ch not in charsToSuppress:
			self._shouldReportChars = 1
		else:
			self._shouldReportChars = 0

	def event_caret(self):
		super().event_caret()
		if self._shouldReportChars == 1:
			self._shouldReportChars = 2
		elif self._shouldReportChars == 2:
			self._shouldReportChars = 0
			speech.speakTextInfo(
				self.getPriorCharacter(),
				unit=textInfos.UNIT_CHARACTER,
				reason=controlTypes.OutputReason.CARET
			)
		else:
			return

	def convertText(self, text):
		processor = self.customProcessor
		processedText = ""
		for ch in text:
			if not ch.isspace():
				ch = characterProcessing.processSpeechSymbol(processor.locale, ch)
			processedText += ch
		return processedText

	@script(
		# Translators: message presented in input mode.
		description=_("Opens the symbols dialog for reading characters typed in Perky")
	)
	def script_symbolsDialog(self, gesture):
		gui.mainFrame.popupSettingsDialog(PerkySpeechSymbolsDialog)

	@script(
		# Translators: message presented in input mode.
		description=_("Shows the selected text converted to braille using symbols for the current language")
	)
	def script_showSelectionConvertedToBraille(self, gesture):
		obj = api.getFocusObject()
		try:
			info = obj.makeTextInfo(textInfos.POSITION_SELECTION)
		except (RuntimeError, NotImplementedError):
			info = None
		if not info or info.isCollapsed:
			# Translators: The message reported when there is no selection
			ui.message(_("No selection"))
			return
		selectedText = info.text
		processedText = self.convertText(selectedText)
		languageDescription = languageHandler.getLanguageDescription(self.customProcessor.locale)
		ui.browseableMessage(
			processedText,
			# Translators: title of NVDA message showing text converted to braille.
			_("Text converted to braille symbols (%s)" % languageDescription)
		)

	@script(
		# Translators: message presented in input mode.
		description=_("Shows the selected text in browse mode")
	)
	def script_showSelectedText(self, gesture):
		obj = api.getFocusObject()
		try:
			info = obj.makeTextInfo(textInfos.POSITION_SELECTION)
		except (RuntimeError, NotImplementedError):
			info = None
		if not info or info.isCollapsed:
			# Translators: The message reported when there is no selection
			ui.message(_("No selection"))
			return
		selectedText = info.text
		ui.browseableMessage(
			selectedText,
			_("Raw selected text")
		)


class EnhancedStatusBar(IAccessible):

	role = controlTypes.Role.STATUSBAR


@disableInSecureMode
class AppModule(appModuleHandler.AppModule):

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if DisplayModelEditableText in clsList:
			clsList.insert(0, EnhancedDocument)
			clsList.insert(1, EditableTextWithAutoSelectDetection)
		elif ContentGenericClient in clsList:
			clsList.insert(0, EnhancedStatusBar)
		elif obj.role == controlTypes.Role.DOCUMENT:
			clsList.insert(0, EnhancedDocument)

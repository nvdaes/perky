# -*- coding: UTF-8 -*-
# perky: app module for Perky Duck
# https://www.duxburysystems.com
# Copyright (C) 2024 Noelia Ruiz Martínez, other contributors
# Released under GPL 2

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

addonHandler.initTranslation()


def disableInSecureMode(decoratedCls):
	if globalVars.appArgs.secure:
		return appModuleHandler.AppModule
	return decoratedCls


class EnhancedDocument(KeyboardHandlerBasedTypedCharSupport):

	role = controlTypes.Role.DOCUMENT
	scriptCategory = "Perky Duck"

	@staticmethod
	def convertText(text):
		processedText = ""
		for ch in text:
			if not ch.isspace():
				ch = characterProcessing.processSpeechSymbol(languageHandler.getLanguage(), ch)
			processedText += ch
		return processedText

	def getPriorCharacter(self):
		charInfo = self.makeTextInfo(textInfos.POSITION_CARET).copy()
		charInfo.move(textInfos.UNIT_CHARACTER, -1)
		charInfo.expand(textInfos.UNIT_CHARACTER)
		return charInfo

	def event_gainFocus(self):
		super().event_gainFocus()
		self._shouldReportChars = 0

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
		ui.browseableMessage(
			processedText,
			# Translators: title of NVDA message showing text converted to braille.
			_("Text converted to braille symbols ({languageDescription})").format(
				languageDescription=languageHandler.getLanguageDescription(languageHandler.getLanguage())
			)
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
			# Translators: Title for a message dialog showing raw selected text.
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

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2017 Belledonne Communications SARL
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


import sys
import os
import argparse
import pystache

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'tools'))
import abstractapi
import genapixml as capi
import metaname
import metadoc


class RstTools:
	@staticmethod
	def make_chapter(text):
		return RstTools.make_section(text, char='*', overline=True)
	
	@staticmethod
	def make_section(text, char='=', overline=False):
		size = len(text)
		underline = (char*size)
		lines = [text, underline]
		if overline:
			lines.insert(0, underline)
		return '\n'.join(lines)


class LangInfo:
	def __init__(self, langCode):
		self.langCode = langCode
		self.displayName = LangInfo._lang_code_to_display_name(langCode)
		self.nameTranslator = metaname.Translator.get(langCode)
		self.langTranslator = abstractapi.Translator.get(langCode)
		self.docTranslator = metadoc.SphinxTranslator(langCode)
	
	@staticmethod
	def _lang_code_to_display_name(langCode):
		if langCode == 'C':
			return 'C'
		elif langCode == 'Cpp':
			return 'C++'
		else:
			raise ValueError("Invalid language code: '{0}'".format(langCode))


class SphinxPage(object):
	def __init__(self, lang, langs, filename):
		object.__init__(self)
		self.lang = lang
		self.langs = langs
		self.filename = filename
	
	def _get_namespace_declararor_existence(self):
		return ('namespaceDeclarator' in dir(self.docTranslator))
	
	hasNamespaceDeclarator = property(fget=_get_namespace_declararor_existence)
	
	def _get_language(self):
		return self.lang.displayName
	
	language = property(fget=_get_language)
	
	def _get_current_doc_translator(self):
		return self.lang.docTranslator
	
	docTranslator = property(fget=_get_current_doc_translator)
	
	def make_chapter(self):
		return lambda text: RstTools.make_chapter(pystache.render(text, self))
	
	def make_section(self):
		return lambda text: RstTools.make_section(pystache.render(text, self))
	
	def write_declarator(self):
		return lambda text: self.docTranslator.get_declarator(text)
	
	def write(self, directory):
		r = pystache.Renderer()
		filepath = os.path.join(directory, self.filename)
		with open(filepath, mode='w') as f:
			f.write(r.render(self))
	
	def _get_translated_namespace(self, obj):
		namespace = obj.find_first_ancestor_by_type(abstractapi.Namespace)
		return namespace.name.translate(self.lang.nameTranslator, recursive=True)
	
	def _make_selector(self, obj):
		links = []
		ref = metadoc.Reference(None)
		ref.relatedObject = obj
		for lang in self.langs:
			if lang is self.lang:
				link = lang.displayName
			else:
				link = ref.translate(lang.docTranslator, label=lang.displayName)
			
			links.append(link)
		
		return ' '.join(links)
	
	@staticmethod
	def _classname_to_filename(classname):
		return classname.to_snake_case(fullName=True) + '.rst'


class IndexPage(SphinxPage):
	def __init__(self, lang, langs):
		SphinxPage.__init__(self, lang, langs, 'index.rst')
		self.tocEntries = []
	
	def add_class_entry(self, _class):
		self.tocEntries.append({'entryName': SphinxPage._classname_to_filename(_class.name)})


class EnumsPage(SphinxPage):
	def __init__(self, lang, langs, enums):
		SphinxPage.__init__(self, lang, langs, 'enums.rst')
		self._translate_enums(enums)
	
	def _translate_enums(self, enums):
		self.enums = []
		for enum in enums:
			translatedEnum = {
				'name'         : enum.name.translate(self.lang.nameTranslator),
				'fullName'     : enum.name.translate(self.lang.nameTranslator, recursive=True),
				'namespace'    : self._get_translated_namespace(enum),
				'briefDesc'    : enum.briefDescription.translate(self.docTranslator),
				'enumerators'  : self._translate_enum_values(enum),
				'selector'    : self._make_selector(enum)
			}
			translatedEnum['sectionName'] = RstTools.make_section(translatedEnum['name'])
			self.enums.append(translatedEnum)
	
	def _translate_enum_values(self, enum):
		translatedEnumerators = []
		for enumerator in enum.enumerators:
			translatedValue = {
				'name'      : enumerator.name.translate(self.lang.nameTranslator),
				'briefDesc' : enumerator.briefDescription.translate(self.docTranslator),
				'value'     : enumerator.translate_value(self.lang.langTranslator),
				'selector' : self._make_selector(enumerator)
			}
			translatedEnumerators.append(translatedValue)
		
		return translatedEnumerators


class ClassPage(SphinxPage):
	def __init__(self, _class, lang, langs):
		filename = SphinxPage._classname_to_filename(_class.name)
		SphinxPage.__init__(self, lang, langs, filename)
		self.namespace = self._get_translated_namespace(_class)
		self.className = _class.name.translate(self.lang.nameTranslator)
		self.fullClassName = _class.name.translate(self.lang.nameTranslator, recursive=True)
		self.briefDoc = _class.briefDescription.translate(self.docTranslator, namespace=_class.name)
		self.detailedDoc = _class.detailedDescription.translate(self.docTranslator, namespace=_class.name) if _class.detailedDescription is not None else None
		self.methods = self._translate_methods(_class.instanceMethods, namespace=_class.name)
		self.classMethods = self._translate_methods(_class.classMethods, namespace=_class.name)
		self.selector = self._make_selector(_class)
	
	def _has_methods(self):
		return len(self.methods) > 0
	
	def _has_class_methods(self):
		return len(self.classMethods)
	
	hasMethods = property(fget=_has_methods)
	hasClassMethods = property(fget=_has_class_methods)
	
	def _translate_methods(self, methods, **kargs):
		translatedMethods = []
		for method in methods:
			methAttr = {
				'prototype'    : method.translate_as_prototype(self.lang.langTranslator),
				'briefDoc'     : method.briefDescription.translate(self.docTranslator, **kargs),
				'detailedDoc'  : method.detailedDescription.translate(self.docTranslator, **kargs),
				'selector'     : self._make_selector(method)
			}
			translatedMethods.append(methAttr)
		return translatedMethods


class DocGenerator:
	def __init__(self, api):
		self.api = api
		self.languages = [
			LangInfo('C'),
			LangInfo('Cpp')
		]
	
	def generate(self, outputdir):
		for lang in self.languages:
			subdirectory = lang.langCode.lower()
			directory = os.path.join(args.outputdir, subdirectory)
			if not os.path.exists(directory):
				os.mkdir(directory)
			
			enumsPage = EnumsPage(lang, self.languages, absApiParser.enumsIndex.values())
			enumsPage.write(directory)
			
			indexPage = IndexPage(lang, self.languages)
			for _class in absApiParser.classesIndex.values():
				page = ClassPage(_class, lang, self.languages)
				page.write(directory)
				indexPage.add_class_entry(_class)
			
			indexPage.write(directory)


if __name__ == '__main__':
	argparser = argparse.ArgumentParser(description='Generate a sphinx project to generate the documentation of Linphone Core API.')
	argparser.add_argument('xmldir', type=str, help='directory holding the XML documentation of the C API generated by Doxygen')
	argparser.add_argument('-o --output', type=str, help='directory into where Sphinx source files will be written', dest='outputdir', default='.')
	args = argparser.parse_args()

	cProject = capi.Project()
	cProject.initFromDir(args.xmldir)
	cProject.check()

	absApiParser = abstractapi.CParser(cProject)
	absApiParser.parse_all()
	
	docGenerator = DocGenerator(absApiParser)
	docGenerator.generate(args.outputdir)

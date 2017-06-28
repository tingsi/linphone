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

import metaname
import abstractapi


class Nil:
	pass


class Reference:
	def __init__(self, cname):
		self.cname = cname
		self.relatedObject = None
	
	def translate(self, docTranslator, **params):
		return docTranslator.translate_reference(self, **params)


class ClassReference(Reference):
	def resolve(self, api):
		try:
			self.relatedObject = api.classesIndex[self.cname]
		except KeyError:
			print('doc reference pointing on an unknown object ({0})'.format(self.cname))


class FunctionReference(Reference):
	def resolve(self, api):
		try:
			self.relatedObject = api.methodsIndex[self.cname]
		except KeyError:
			print('doc reference pointing on an unknown object ({0})'.format(self.cname))


class Paragraph:
	def __init__(self):
		self.parts = []
	
	def resolve_all_references(self, api):
		for part in self.parts:
			if isinstance(part, Reference):
				part.resolve(api)
	
	def translate(self, docTranslator, **kargs):
		return docTranslator._translate_paragraph(self, **kargs)


class Section:
	def __init__(self, kind):
		self.kind = kind
		self.paragraph = None
	
	def translate(self, docTranslator, **kargs):
		return docTranslator._translate_section(self, **kargs)


class Description:
	def __init__(self):
		self.paragraphs = []
	
	def resolve_all_references(self, api):
		for paragraph in self.paragraphs:
			paragraph.resolve_all_references(api)
	
	def translate(self, translator, **kargs):
		return translator.translate_description(self, **kargs)


class Parser:
	def parse_description(self, node):
		desc = Description()
		for paraNode in node.findall('./para'):
			paragraph = self._parse_paragraph(paraNode)
			if paragraph is not None:
				desc.paragraphs.append(paragraph)
		return desc
	
	def _parse_paragraph(self, node):
		paragraph = Paragraph()
		
		text = node.text
		if text is not None:
			paragraph.parts.append(text)
		
		for partNode in node.findall('*'):
			if partNode.tag == 'ref':
				ref = self._parse_reference(partNode)
				if ref is not None:
					paragraph.parts.append(ref)
			elif partNode.tag == 'simplesect':
				paragraph.parts.append(self._parse_simple_section(partNode))
			else:
				text = partNode.text
				if text is not None:
					paragraph.parts.append(text)
			
			text = partNode.tail
			if text is not None:
				paragraph.parts.append(text)
		
		return paragraph
	
	def _parse_simple_section(self, sectionNode):
		section = Section(sectionNode.get('kind'))
		para = sectionNode.find('./para')
		section.paragraph = self._parse_paragraph(para)
		return section
	
	def _parse_reference(self, node):
		if node.text.endswith('()'):
			return FunctionReference(node.text[0:-2])
		else:
			return ClassReference(node.text)


class Translator:
	def __init__(self, langCode):
		self.textWidth = 80
		self.nameTranslator = metaname.Translator.get(langCode)
	
	def translate_description(self, description, **kargs):
		if description is None:
			return None
		
		paras = []
		for para in description.paragraphs:
			paras.append(para.translate(self, **kargs))
		
		lines = self._paragraphs_to_lines(paras)
		self._tag_as_brief(lines)
		lines = self._crop_text(lines, self.textWidth)
		
		translatedDoc = {'lines': []}
		for line in lines:
			translatedDoc['lines'].append({'line': line})
			
		return translatedDoc
	
	def _translate_paragraph(self, para, **kargs):
		strPara = ''
		for part in para.parts:
			try:
				if isinstance(part, str):
					strPara += part
				else:
					strPara += part.translate(self, **kargs)
			except TranslationError as e:
				print('error: {0}'.format(e.msg()))
		
		return strPara
	
	def _paragraphs_to_lines(self, paragraphs):
		lines = []
		for para in paragraphs:
			if para is not paragraphs[0]:
				lines.append('')
			lines += para.split(sep='\n')
		return lines
	
	def _crop_text(self, inputLines, width):
		outputLines = []
		for line in inputLines:
			outputLines += self._split_line(line, width)
		return outputLines
	
	def _split_line(self, line, width):
		firstNonTab = next((c for c in line if c != '\t'), None)
		tabCount = line.index(firstNonTab) if firstNonTab is not None else 0
		linePrefix = ('\t' * tabCount)
		line = line[tabCount:]
		
		lines = []
		while len(line) > width:
			cutIndex = line.rfind(' ', 0, width)
			if cutIndex != -1:
				lines.append(line[0:cutIndex])
				line = line[cutIndex+1:]
			else:
				cutIndex = width
				lines.append(line[0:cutIndex])
				line = line[cutIndex:]
		
		lines.append(line)
		
		return [linePrefix + line for line in lines]
	
	def _tag_as_brief(self, lines):
		pass


class TranslationError(Exception):
	pass


class ReferenceTranslationError(TranslationError):
	def __init__(self, refName):
		Exception.__init__(self, refName)
	
	def msg(self):
		return '{0} reference could not been translated'.format(self.args[0])


class DoxygenTranslator(Translator):
	def _tag_as_brief(self, lines):
		if len(lines) > 0:
			lines[0] = '@brief ' + lines[0]
	
	def translate_reference(self, ref, **kargs):
		if isinstance(ref.relatedObject, (abstractapi.Class, abstractapi.Enum)):
			return '#' + ref.relatedObject.name.translate(self.nameTranslator, recursive=True)
		elif isinstance(ref.relatedObject, abstractapi.Method):
			return ref.relatedObject.name.translate(self.nameTranslator, recursive=True) + '()'
		else:
			raise ReferenceTranslationError(ref.cname)
	
	def _translate_section(self, section, **kargs):
		return '@{0} {1}'.format(
			section.kind,
			self._translate_paragraph(section.paragraph, **kargs)
		)


class SphinxTranslator(Translator):
	def __init__(self, langCode):
		Translator.__init__(self, langCode)
		if isinstance(self.nameTranslator, metaname.CTranslator):
			self.namespace = 'c'
			self.classDeclarator = 'type'
			self.methodDeclarator = 'function'
			self.enumDeclarator = 'type'
			self.enumeratorDeclarator = 'var'
			self.enumeratorReferencer = 'data'
		elif isinstance(self.nameTranslator, metaname.CppTranslator):
			self.namespace = 'cpp'
			self.classDeclarator = 'class'
			self.methodDeclarator = 'function'
			self.enumDeclarator = 'enum'
			self.enumeratorDeclarator = 'enumerator'
			self.namespaceDeclarator = 'namespace'
		else:
			TypeError('not suppored name translator: ' + str(self.nameTranslator))
		
		self.methodReferencer = 'func'
	
	def get_declarator(self, typeName):
		try:
			attrName = typeName + 'Declarator'
			declarator = getattr(self, attrName)
			return '{0}:{1}'.format(self.namespace, declarator)
		except AttributeError:
			raise ValueError("'{0}' declarator type not supported".format(typeName))
	
	def get_referencer(self, typeName):
		try:
			attrName = typeName + 'Referencer'
			if attrName in dir(self):
				referencer = getattr(self, attrName)
				return '{0}:{1}'.format(self.namespace, referencer)
			else:
				return self.get_declarator(typeName)
		except AttributeError:
			raise ValueError("'{0}' referencer type not supported".format(typeName))
	
	def translate_reference(self, ref, label=None, namespace=None):
		if ref.relatedObject is None:
			raise ReferenceTranslationError(ref.cname)
		
		commonName = metaname.Name.find_common_parent(ref.relatedObject.name, namespace) if namespace is not None else None
		_label = label if label is not None else ref.relatedObject.name.translate(self.nameTranslator, recursive=True, topAncestor=commonName)
		if isinstance(ref, FunctionReference):
			_label += '()'
		
		return ':{tag}:`{label} <{ref}>`'.format(
			tag=self._sphinx_ref_tag(ref),
			ref=ref.relatedObject.name.translate(self.nameTranslator, recursive=True),
			label=_label
		)
	
	def _translate_section(self, section, **kargs):
		strPara = self._translate_paragraph(section.paragraph, **kargs)
		if section.kind == 'see':
			kind = 'seealso'
		else:
			kind = section.kind
		return '.. {0}::\n\t\n\t{1}'.format(kind, strPara)
	
	def _sphinx_ref_tag(self, ref):
		typeName = type(ref.relatedObject).__name__.lower()
		return self.get_referencer(typeName)


class SandcastleCSharpTranslator(Translator):
	def __init__(self):
		Translator.__init__(self, None)
	
	def _tag_as_brief(self, lines):
		if len(lines) > 0:
			lines.insert(0, '<summary>')
			lines.append('</summary>')

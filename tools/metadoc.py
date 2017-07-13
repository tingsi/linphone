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
import re


class Nil:
	pass


class Reference:
	def __init__(self, cname):
		self.cname = cname
		self.relatedObject = None
	
	def translate(self, docTranslator, label=None, **kargs):
		return docTranslator.translate_reference(self, **kargs)


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
			elif isinstance(part, (Section, ParameterList)):
				part.resolve_all_references(api)
	
	def translate(self, docTranslator, **kargs):
		return docTranslator._translate_paragraph(self, **kargs)


class Section:
	def __init__(self, kind):
		self.kind = kind
		self.paragraph = None
	
	def resolve_all_references(self, api):
		if self.paragraph is not None:
			self.paragraph.resolve_all_references(api)
	
	def translate(self, docTranslator, **kargs):
		return docTranslator._translate_section(self, **kargs)


class ParameterDescription:
	def __init__(self, name, desc):
		self.name = name
		self.desc = desc


class ParameterList:
	def __init__(self):
		self.parameters = []
	
	def resolve_all_references(self, api):
		for parameter in self.parameters:
			if parameter.desc is not None:
				parameter.desc.resolve_all_references(api)
	
	def translate(self, docTranslator, **kargs):
		return docTranslator._translate_parameter_list(self, **kargs)


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
		if node is None:
			return None
		
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
			elif partNode.tag == 'parameterlist' and partNode.get('kind') == 'param':
				paragraph.parts.append(self._parse_parameter_list(partNode))
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
	
	def _parse_parameter_list(self, paramListNode):
		paramList = ParameterList()
		for paramItemNode in paramListNode.findall('./parameteritem'):
			name = paramItemNode.find('./parameternamelist/parametername').text
			desc = self.parse_description(paramItemNode.find('parameterdescription'))
			paramList.parameters.append(ParameterDescription(name, desc))
		return paramList
	
	def _parse_reference(self, node):
		if node.text.endswith('()'):
			return FunctionReference(node.text[0:-2])
		else:
			return ClassReference(node.text)


class Translator:
	def __init__(self, langCode):
		self.textWidth = 80
		self.nameTranslator = metaname.Translator.get(langCode)
	
	def translate_description(self, description, tagAsBrief=False, namespace=None):
		if description is None:
			return None
		
		paras = self._translate_description(description, namespace=namespace)
		
		lines = self._paragraphs_to_lines(paras)
		
		if tagAsBrief:
			self._tag_as_brief(lines)
		
		lines = self._crop_text(lines, self.textWidth)
		
		translatedDoc = {'lines': []}
		for line in lines:
			translatedDoc['lines'].append({'line': line})
		
		return translatedDoc
	
	def translate_reference(self, ref, namespace=None):
		if ref.relatedObject is None:
			raise ReferenceTranslationError(ref.cname)
		commonName = metaname.Name.find_common_parent(ref.relatedObject.name, namespace) if namespace is not None else None
		return ref.relatedObject.name.translate(self.nameTranslator, recursive=True, topAncestor=commonName)
	
	def _translate_description(self, desc, namespace=None):
		paras = []
		for para in desc.paragraphs:
			paras.append(para.translate(self, namespace=namespace))
		return paras
	
	def _translate_paragraph(self, para, namespace=None):
		strPara = ''
		for part in para.parts:
			try:
				if isinstance(part, str):
					strPara += part
				else:
					strPara += part.translate(self, namespace=namespace)
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
	
	def _split_line(self, line, width, indent=False):
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
		
		if indent:
			lines = [line if line is lines[0] else '\t' + line for line in lines]
		
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
	
	def translate_reference(self, ref, namespace=None):
		refStr = Translator.translate_reference(self, ref, namespace=namespace)
		if isinstance(ref.relatedObject, (abstractapi.Class, abstractapi.Enum)):
			return '#' + refStr
		elif isinstance(ref.relatedObject, abstractapi.Method):
			return refStr + '()'
		else:
			raise ReferenceTranslationError(ref.cname)
	
	def _translate_section(self, section, namespace=None):
		return '@{0} {1}'.format(
			section.kind,
			self._translate_paragraph(section.paragraph, namespace=namespace)
		)
	
	def _translate_parameter_list(self, parameterList, namespace=None):
		text = ''
		for paramDesc in parameterList.parameters:
			desc = self._translate_description(paramDesc.desc, namespace=namespace) if paramDesc.desc is not None else ['']
			text = ('@param {0} {1}'.format(paramDesc.name, desc[0]))
		return text


class SphinxTranslator(Translator):
	def __init__(self, langCode):
		Translator.__init__(self, langCode)
		if langCode == 'C':
			self.domain = 'c'
			self.classDeclarator = 'type'
			self.methodDeclarator = 'function'
			self.enumDeclarator = 'type'
			self.enumeratorDeclarator = 'var'
			self.enumeratorReferencer = 'data'
			self.methodReferencer = 'func'
		elif langCode == 'Cpp':
			self.domain = 'cpp'
			self.classDeclarator = 'class'
			self.methodDeclarator = 'function'
			self.enumDeclarator = 'enum'
			self.enumeratorDeclarator = 'enumerator'
			self.namespaceDeclarator = 'namespace'
			self.methodReferencer = 'func'
		elif langCode == 'CSharp':
			self.domain = 'csharp'
			self.classDeclarator = 'class'
			self.methodDeclarator = 'method'
			self.enumDeclarator = 'enum'
			self.enumeratorDeclarator = 'value'
			self.namespaceDeclarator = 'namespace'
			self.methodReferencer = 'meth'
		else:
			raise ValueError('invalid language code: {0}'.format(langCode))
	
	def get_declarator(self, typeName):
		try:
			attrName = typeName + 'Declarator'
			declarator = getattr(self, attrName)
			return '{0}:{1}'.format(self.domain, declarator)
		except AttributeError:
			raise ValueError("'{0}' declarator type not supported".format(typeName))
	
	def get_referencer(self, typeName):
		try:
			attrName = typeName + 'Referencer'
			if attrName in dir(self):
				referencer = getattr(self, attrName)
				return '{0}:{1}'.format(self.domain, referencer)
			else:
				return self.get_declarator(typeName)
		except AttributeError:
			raise ValueError("'{0}' referencer type not supported".format(typeName))
	
	def translate_reference(self, ref, label=None, namespace=None):
		strRef = Translator.translate_reference(self, ref)
		kargs = {
			'tag'   : self._sphinx_ref_tag(ref),
			'ref'   : strRef,
		}
		kargs['label'] = label if label is not None else Translator.translate_reference(self, ref, namespace=namespace)
		if isinstance(ref, FunctionReference):
			kargs['label'] += '()'
		
		return ':{tag}:`{label} <{ref}>`'.format(**kargs)
	
	def _translate_section(self, section, namespace=None):
		strPara = self._translate_paragraph(section.paragraph, namespace=namespace)
		if section.kind == 'see':
			kind = 'seealso'
		else:
			kind = section.kind
		
		if section.kind == 'return':
			return ':return: {0}'.format(strPara)
		else:
			return '.. {0}::\n\t\n\t{1}'.format(kind, strPara)
	
	def _translate_parameter_list(self, parameterList, namespace=None):
		text = ''
		for paramDesc in parameterList.parameters:
			desc = self._translate_description(paramDesc.desc, namespace=namespace) if paramDesc.desc is not None else ['']
			text = (':param {0}: {1}'.format(paramDesc.name, desc[0]))
		return text
	
	def _sphinx_ref_tag(self, ref):
		typeName = type(ref.relatedObject).__name__.lower()
		return self.get_referencer(typeName)
	
	def _split_line(self, line, width):
		if re.match('\t*:param\s+\w+:', line) is None:
			return Translator._split_line(self, line, width)
		else:
			return Translator._split_line(self, line, width, indent=True)
		


class SandCastleTranslator(Translator):
	def _tag_as_brief(self, lines):
		if len(lines) > 0:
			lines.insert(0, '<summary>')
			lines.append('</summary>')
	
	def translate_reference(self, ref, namespace=None):
		refStr = Translator.translate_reference(self, ref, namespace=namespace)
		if isinstance(ref, FunctionReference):
			refStr += '()'
		return '<see cref="{0}" />'.format(refStr)

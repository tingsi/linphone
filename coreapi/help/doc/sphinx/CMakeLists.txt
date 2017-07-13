############################################################################
# CMakeLists.txt
# Copyright (C) 2017  Belledonne Communications, Grenoble France
#
############################################################################
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
#
############################################################################

if (ENABLE_DOC)
	set(GENERATED_SPHINX_SOURCES ${CMAKE_CURRENT_BINARY_DIR}/source/c/index.rst
		${CMAKE_CURRENT_BINARY_DIR}/source/cpp/index.rst
		${CMAKE_CURRENT_BINARY_DIR}/source/csharp/index.rst
	)
	set(PYTHON_SCRIPTS gendoc.py
		${linphone_SOURCE_DIR}/tools/abstractapi.py
		${linphone_SOURCE_DIR}/tools/genapixml.py
		${linphone_SOURCE_DIR}/tools/metadoc.py
		${linphone_SOURCE_DIR}/tools/metaname.py
	)
	set(MUSTACHE_TEMPLATES class_page.mustache
		enums_page.mustache
		index_page.mustache
	)
	configure_file(conf.py.in source/conf.py)
	configure_file(source/index.rst source/index.rst COPYONLY)
	add_custom_command(OUTPUT ${GENERATED_SPHINX_SOURCES}
		COMMAND ${PYTHON_EXECUTABLE} '${CMAKE_CURRENT_SOURCE_DIR}/gendoc.py' '${LINPHONE_DOXYGEN_XML_DIR}' -o 'source'
		DEPENDS ${PYTHON_SCRIPTS}
		${MUSTACHE_TEMPLATES}
		${LINPHONE_DOXYGEN_XML_DIR}/index.xml
		linphone-doc
	)
	add_custom_command(OUTPUT build/html/index.html
		COMMAND ${PYTHON_EXECUTABLE} -msphinx -M html 'source' 'build'
		DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/source/conf.py
		${CMAKE_CURRENT_BINARY_DIR}/source/index.rst
		${GENERATED_SPHINX_SOURCES}
	)
	add_custom_target(sphinx-doc ALL DEPENDS build/html/index.html)
endif()

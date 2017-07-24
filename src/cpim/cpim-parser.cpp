/*
 * cpim-parser.cpp
 * Copyright (C) 2017  Belledonne Communications SARL
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <belr/abnf.hh>
#include <belr/grammarbuilder.hh>

#include "linphone/core.h"

#include "cpim-grammar.h"
#include "cpim-message.h"
#include "cpim-parser.h"

using namespace std;

using namespace Linphone;

// =============================================================================

class HeaderParser {
public:
  virtual ~HeaderParser ();
  void setValue (const string &value) {
    mValue = value;
  }

protected:
  string mName;

private:
  string mValue;
};

#define MAKE_CORE_HEADER_PARSER(CLASS, NAME) \
  class CLASS ## HeaderParser : public HeaderParser {};

class GenericHeaderParser : public HeaderParser {
public:
  void setName (const string &name) {
    mName = name;
  }
};

MAKE_CORE_HEADER_PARSER(From, "From");
MAKE_CORE_HEADER_PARSER(To, "To");
MAKE_CORE_HEADER_PARSER(Cc, "cc");
MAKE_CORE_HEADER_PARSER(DateTime, "DateTime");
MAKE_CORE_HEADER_PARSER(Subject, "Subject");
MAKE_CORE_HEADER_PARSER(Ns, "NS");
MAKE_CORE_HEADER_PARSER(Require, "Require");

#undef MAKE_CORE_HEADER_PARSER

// -----------------------------------------------------------------------------

class MessageParser {
public:
  void setMimeHeaders (const shared_ptr<list<HeaderParser> > &mimeHeaders);
  void setMessageHeaders (const shared_ptr<list<HeaderParser> > &messageHeaders);
  void setContent (const string &content);
};

// -----------------------------------------------------------------------------

class Cpim::ParserPrivate : public ObjectPrivate {
public:
  shared_ptr<belr::Grammar> grammar;
};

Cpim::Parser::Parser () : Singleton(new ParserPrivate) {
  L_D(Parser);

  d->grammar = belr::ABNFGrammarBuilder().createFromAbnf(
      LinphonePrivate::Cpim::getGrammar(),
      make_shared<belr::CoreRules>()
    );
  if (!d->grammar)
    ms_fatal("Unable to build CPIM grammar.");
}

shared_ptr<Cpim::Message> Cpim::Parser::parseMessage (const string &input) {
  L_D(Parser);

  typedef void (list<HeaderParser>::*pushPtr)(const HeaderParser &value);

  belr::Parser<shared_ptr<MessageParser> > parser(d->grammar);
  parser.setHandler(
    "Message", belr::make_fn(make_shared<MessageParser> )
  )->setCollector(
    "Mime-Headers", belr::make_sfn(&MessageParser::setMimeHeaders)
  )->setCollector(
    "Message-Headers", belr::make_sfn(&MessageParser::setMessageHeaders)
  );

  parser.setHandler(
    "Mime-Headers", belr::make_fn(make_shared<list<HeaderParser> > )
  )->setCollector(
    "Header-generic", belr::make_sfn(static_cast<pushPtr>(&list<HeaderParser>::push_back))
  )->setCollector(
    "ContentType-header", belr::make_sfn(static_cast<pushPtr>(&list<HeaderParser>::push_front))
  );

  parser.setHandler(
    "Header-generic", belr::make_fn(make_shared<GenericHeaderParser> )
  )->setCollector(
    "Header-name", belr::make_sfn(&GenericHeaderParser::setName)
  )->setCollector(
    "Header-value", belr::make_sfn(&GenericHeaderParser::setValue)
  );

  parser.setHandler(
    "ContentType-header", []() -> shared_ptr<GenericHeaderParser> {
      shared_ptr<GenericHeaderParser> parser = make_shared<GenericHeaderParser>();
      parser->setName("ContentType");
      parser->setValue("Message/CPIM");
      return parser;
    });

  size_t parsedSize = 0;
  shared_ptr<MessageParser> messageParser = parser.parseInput("Message", input, &parsedSize);
  if (!messageParser) {
    ms_warning("Unable to parse message.");
    return nullptr;
  }
}

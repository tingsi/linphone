/*
 * cpim-message.c
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

#include "cpim-message.h"

using namespace std;

using namespace Linphone;

// =============================================================================

// dynamic_cast

// -----------------------------------------------------------------------------

class Cpim::MessagePrivate : public ObjectPrivate {
public:
  shared_ptr<const list<Cpim::Header> > mimeHeaders;
  shared_ptr<const list<Cpim::Header> > messageHeaders;
  string content;
};

Cpim::Message::Message () : Object(new Cpim::MessagePrivate) {}

shared_ptr<const list<Cpim::Header> > Cpim::Message::getMimeHeaders () const {
  L_D(const Message);
  return d->mimeHeaders;
}

bool Cpim::Message::setMimeHeaders (const shared_ptr<list<Header> > &mimeHeaders) {
  return false;
}

shared_ptr<const list<Cpim::Header> > Cpim::Message::getMessageHeaders () const {
  L_D(const Message);
  return d->messageHeaders;
}

bool Cpim::Message::setMessageHeaders (const shared_ptr<list<Header> > &messageHeaders) {
  return false;
}

string Cpim::Message::getContent () const {
  L_D(const Message);
  return d->content;
}

bool Cpim::Message::setContent (const string &content) {
  return false;
}

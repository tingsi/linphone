/*
 * cpim-message.h
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

#ifndef _CPIM_MESSAGE_H_
#define _CPIM_MESSAGE_H_

#include <list>
#include <string>
#include <memory>

#include "object/object.h"

// =============================================================================

#define MAKE_CORE_HEADER(CLASS, NAME) \
  class CLASS ## Header : public CoreHeader { \
  public: \
    inline std::string getName() const override { \
      return NAME; \
    } \
    std::string getValue() const override; \
    bool setValue(const std::string &value) override; \
  private: \
    L_DISABLE_COPY(CLASS ## Header); \
  };

namespace Linphone {
  namespace Cpim {
    class CoreHeaderPrivate;
    class GenericHeaderPrivate;
    class MessagePrivate;

    // -------------------------------------------------------------------------
    // Headers.
    // -------------------------------------------------------------------------

    class Header : public Object {
    public:
      virtual ~Header () = 0;

      virtual std::string getName () const = 0;
      virtual std::string getValue () const = 0;
      virtual bool setValue (const std::string &value) = 0;

    private:
      L_DISABLE_COPY(Header);
    };

    class CoreHeader : public Header {
    public:
      virtual ~CoreHeader () = 0;

    private:
      L_DECLARE_PRIVATE(CoreHeader);
      L_DISABLE_COPY(CoreHeader);
    };

    MAKE_CORE_HEADER(From, "From");
    MAKE_CORE_HEADER(To, "To");
    MAKE_CORE_HEADER(Cc, "cc");
    MAKE_CORE_HEADER(DateTime, "DateTime");
    MAKE_CORE_HEADER(Subject, "Subject");
    MAKE_CORE_HEADER(Ns, "NS");
    MAKE_CORE_HEADER(Require, "Require");

    class GenericHeader : public Header {
    public:
      std::string getName () const override;
      std::string setName ();
      std::string getValue () const override;
      bool setValue (const std::string &value) override;

    private:
      L_DECLARE_PRIVATE(GenericHeader);
      L_DISABLE_COPY(GenericHeader);
    };

    // -------------------------------------------------------------------------
    // Message.
    // -------------------------------------------------------------------------

    class Message : public Object {
    public:
      Message ();

      std::shared_ptr<const std::list<Header> > getMimeHeaders () const;
      bool setMimeHeaders (const std::shared_ptr<std::list<Header> > &mimeHeaders);

      std::shared_ptr<const std::list<Header> > getMessageHeaders () const;
      bool setMessageHeaders (const std::shared_ptr<std::list<Header> > &messageHeaders);

      std::string getContent () const;
      bool setContent (const std::string &content);

    private:
      L_DECLARE_PRIVATE(Message);
      L_DISABLE_COPY(Message);
    };
  }
}

#undef MAKE_HEADER

#endif // ifndef _CPIM_MESSAGE_H_

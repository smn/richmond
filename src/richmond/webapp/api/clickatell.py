#!/usr/local/bin/python
"""
python module which can be used to send SMS messages via the Clickatell HTTP/S API
Interface on https://api.clickatell.com/

See U{the Clickatell HTTP/S API documentation<http://www.clickatell.com/downloads/http/Clickatell_http_2.2.7.pdf>}
for more information on how their HTTP/S API interface works

*** WARNING *** DANGER WILL ROBINSON *** THIS CODE IS UNDERGOING MAJOR CHANGES AND THE INTERFACES MAY CHANGE AT ANYTIME PRIOR TO AN INITIAL RELEASE BEING MADE ***

$Id: clickatell.py 714 2006-09-19 23:10:36Z jacques $
"""
# from http://www.powertrip.co.za/code/python/clickatell.py

import pycurl

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

__author__      = "Jacques Marneweck <jacques@php.net>"
__version__     = "0.1.1-alpha"
__copyright__   = "Copyright (c) 2006 Jacques Marneweck.  All rights reserved."
__license__     = "The MIT License"

class ClickatellError (Exception):
    """
    Base class for Clickatell errors
    """

class ClickatellAuthenticationError (ClickatellError):
    pass

class Clickatell(object):
    """
    Provides a wrapper around the Clickatell HTTP/S API interface
    """

    def __init__ (self, username, password, api_id):
        """
        Initialise the Clickatell class

        Expects:
         - username - your Clickatell Central username
         - password - your Clickatell Central password
         - api_id - your Clickatell Central HTTP API identifier
        """
        self.ch = pycurl.Curl()
        self.has_authed = False

        self.username = username
        self.password = password
        self.api_id = api_id

        self.session_id = None

    def auth (self):
        """
        Authenticate against the Clickatell API server
        """
        url = 'https://api.clickatell.com/http/auth'
 
        post = [
            ('user', self.username),
            ('password', self.password),
            ('api_id', self.api_id),
        ]

        result = self.curl (url, post)

        if result[0] == 'OK':
            assert (32 == len(result[1]))
            self.session_id = result[1]
            self.has_authed = True
            return True
        else:
            return False

    def getbalance (self):
        """
        Get the number of credits remaining at Clickatell
        """
        if self.has_authed == False:
            self.auth()

        url = 'https://api.clickatell.com/http/getbalance'
 
        post = [
            ('session_id', self.session_id),
        ]

        result = self.curl (url, post)
        if result[0] == 'Credit':
            assert (0 <= result[1])
            return result[1]
        else:
            return False

    def getmsgcharge (self, apimsgid):
        """
        Get the message charge for a previous sent message
        """
        if self.has_authed == False:
            self.auth()

        assert (32 == len(apimsgid))

        url = 'https://api.clickatell.com/http/getmsgcharge'
 
        post = [
            ('session_id', self.session_id),
            ('apimsgid', apimsgid),
        ]

        result = self.curl (url, post)
        result = ' '.join(result).split(' ')

        if result[0] == 'apiMsgId':
            assert (apimsgid == result[1])
            assert (0 <= result[3])
            return result[3]
        else:
            return False

    def ping (self):
        """
        Ping the Clickatell API interface to keep the session open
        """
        if self.has_authed == False:
            self.auth()

        url = 'https://api.clickatell.com/http/ping'
 
        post = [
            ('session_id', self.session_id),
        ]

        result = self.curl (url, post)

        if result[0] == 'OK':
            return True
        else:
            self.has_authed = False
            return False

    def sendmsg (self, message):
        """
        Send a mesage via the Clickatell API server

        message = {
            'to': 'to_msisdn',
            'sender': 'from_msisdn',
            'text': 'This is a test message',
            'msg_type': 'SMS_TEXT',
            'climsgid': 'random_md5_hash',
        }

        result = clickatell.sendmsg(message)
        if result[0] == True:
            print "Message was sent successfully"
            print "Clickatell returned %s" % result[1]
        else:
            print "Message was not sent"

        """
        if self.has_authed == False:
            self.auth()

        assert (message['msg_type'] in ('SMS_TEXT', 'SMS_FLASH'))

        url = 'https://api.clickatell.com/http/sendmsg'

        print message

        post = [
            ('session_id', self.session_id),
            ('to', message['to']),
            ('text', message['text']),
            ('from', message['sender']),
            ('max_credits', '1'),
            ('deliv_ack', '1'),
            ('callback', '3'),
            ('climsgid', message['climsgid']),
        ]

        post.append(('foobar', 'fooof'))

        print post

        result = self.curl (url, post)

        if result[0] == 'ID':
            print result[1]
            assert (result[1])
            return (True, result[1])
        else:
            return (False, )

    def tokenpay (self, voucher):
        """
        Redeem a voucher via the Clickatell API interface
        """
        if self.has_authed == False:
            self.auth()

        assert (16 == len(voucher))

        url = 'https://api.clickatell.com/http/token_pay'
 
        post = [
            ('session_id', self.session_id),
            ('token', voucher),
        ]

        result = self.curl (url, post)

        if result[0] == 'OK':
            return True
        else:
            return False

    def curl (self, url, post):
        """
        Inteface for sending web requests to the Clickatell API Server
        """
        data = StringIO()
        self.ch.setopt(pycurl.URL, url)
        self.ch.setopt(pycurl.VERBOSE, 0)
        self.ch.setopt(pycurl.SSLVERSION, 3)
        self.ch.setopt(pycurl.SSL_VERIFYPEER, 1)
        self.ch.setopt(pycurl.SSL_VERIFYHOST, 2)
        self.ch.setopt(pycurl.HTTPHEADER, [
                "User-Agent: py-clickatell %s" % (__version__),
                "Accept:"
            ])
        self.ch.setopt(pycurl.WRITEFUNCTION, data.write)
        self.ch.setopt(pycurl.HTTPPOST, post)
        self.ch.setopt(pycurl.FOLLOWLOCATION, 1)

        try:
            result = self.ch.perform()
        except pycurl.error, v:
            print v

        return data.getvalue().split(": ")
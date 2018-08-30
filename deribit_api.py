# -*- coding: utf-8 -*-

import time, hashlib, requests, base64, sys
from collections import OrderedDict


import asyncio
import base64
import collections
import datetime
import hashlib
import json
import logging
import random
import socket
import sys
import threading
import time
import typing
import weakref

try:
    from urllib.parse import urlparse, urlunparse, urljoin
except ImportError: # had a different name in python2
    from urlparse import urlparse, urlunparse, urljoin

try:
    import queue
except ImportError: # had a different name in python2
    import Queue as queue  

try:
    import websocket

    # There is a different package, which also uses the websocket namespace.
    # Make sure we actually have the right library.
    assert websocket.create_connection  
except ImportError:
    # Allow absence of websocket library, as it is a dependency introduced
    # in a minor update
    websocket = None
    # Users can run `pip install websocket-client` to install it



class RestClient(object):
    def __init__(self, key=None, secret=None, url=None):
        self.key = key
        self.secret = secret
        self.session = requests.Session()

        if url:
            self.url = url
        else:
            self.url = "https://www.deribit.com"

    def request(self, action, data):
        response = None

        if action.startswith("/api/v1/private/"):
            if self.key is None or self.secret is None:
                raise Exception("Key or secret empty")

            signature = self.generate_signature(action, data)
            response = self.session.post(self.url + action, data=data, headers={'x-deribit-sig': signature}, verify=True)
        else:
            response = self.session.get(self.url + action, params=data, verify=True)
        
        if response.status_code != 200:
            raise Exception("Wrong response code: {0}".format(response.status_code))

        return self._interpret_response(response.json())

    @staticmethod
    def _interpret_response(response):

        if response["success"] == False:
            raise Exception("Failed: " + response["message"])
        
        if "result" in response:
            return response["result"]
        else:
            return response.get("message", "Ok")


    def generate_signature(self, action, data):
        tstamp = int(time.time()* 1000)
        signature_data = {
            '_': tstamp,
            '_ackey': self.key,
            '_acsec': self.secret,
            '_action': action
        }
        signature_data.update(data)
        sorted_signature_data = OrderedDict(sorted(signature_data.items(), key=lambda t: t[0]))


        def converter(data):
            key = data[0]
            value = data[1]
            if isinstance(value, bool):
                return '='.join([str(key), str(value).lower()])
            elif isinstance(value, list):
                return '='.join([str(key), ''.join(value)])
            else:
                return '='.join([str(key), str(value)])

        items = map(converter, sorted_signature_data.items())

        signature_string = '&'.join(items)

        sha256 = hashlib.sha256()
        sha256.update(signature_string.encode("utf-8"))
        sig = self.key + "." + str(tstamp) + "." 
        sig += base64.b64encode(sha256.digest()).decode("utf-8")
        return sig

    def getorderbook(self, instrument):
        return self.request("/api/v1/public/getorderbook", {'instrument': instrument})

    def getinstruments(self):
        return self.request("/api/v1/public/getinstruments", {})


    def getcurrencies(self):
        return self.request("/api/v1/public/getcurrencies", {})


    def getlasttrades(self, instrument, count=None, since=None):
        options = {
            'instrument': instrument
        }

        if since:
            options['since'] = since

        if count:
            options['count'] = count

        return self.request("/api/v1/public/getlasttrades", options)


    def getsummary(self, instrument):
        return self.request("/api/v1/public/getsummary", {"instrument": instrument})


    def index(self):
        return self.request("/api/v1/public/index", {})

    
    def stats(self):
        return self.request("/api/v1/public/stats", {})


    def account(self):
        return self.request("/api/v1/private/account", {})


    def buy(self, instrument, quantity, price, postOnly=None, label=None):
        options = {
            "instrument": instrument,
            "quantity": quantity,
            "price": price
        }
  
        if label:
            options["label"] = label

        if postOnly:
            options["postOnly"] = postOnly

        return self.request("/api/v1/private/buy", options)


    def sell(self, instrument, quantity, price, postOnly=None, label=None):
        options = {
            "instrument": instrument,
            "quantity": quantity,
            "price": price
        }

        if label:
            options["label"] = label
        if postOnly:
            options["postOnly"] = postOnly

        return self.request("/api/v1/private/sell", options)


    def cancel(self, orderId):
        options = {
            "orderId": orderId
        }  

        return self.request("/api/v1/private/cancel", options)


    def cancelall(self, typeDef="all"):
        return self.request("/api/v1/private/cancelall", {"type": typeDef})


    def edit(self, orderId, quantity, price):
        options = {
            "orderId": orderId,
            "quantity": quantity,
            "price": price
        }

        return self.request("/api/v1/private/edit", options)


    def getopenorders(self, instrument=None, orderId=None):
        options = {}

        if instrument:
            options["instrument"] = instrument 
        if orderId:
            options["orderId"] = orderId

        return self.request("/api/v1/private/getopenorders", options)


    def positions(self):
        return self.request("/api/v1/private/positions", {})


    def orderhistory(self, count=None):
        options = {}
        if count:
            options["count"] = count

        return self.request("/api/v1/private/orderhistory", options)


    def tradehistory(self, countNum=None, instrument="all", startTradeId=None):
        options = {
            "instrument": instrument
        }
  
        if countNum:
            options["count"] = countNum
        if startTradeId:
            options["startTradeId"] = startTradeId
        
        return self.request("/api/v1/private/tradehistory", options)


_pending = object()


class WebsocketClient(RestClient):
    def __init__(self, key=None, secret=None, url=None):
        """Instantiates the deribit websocket client.

        Args:
            key:      Your deribit access key
            secret:   Your deribit access secret
            url:      The url to use for connecting to Deribit
        """        
        super(WebsocketClient, self).__init__(key=key, secret=secret, url=url)

        if not websocket:
            # Users can run `pip install websocket-client`` to install it
            raise Exception("Need package websocket-client installed.")

        self._websocket = None

        self._async_results = {}
        self._async_result_available = threading.Condition()
        self._notify_queues = {}
        self._live_order_books = weakref.WeakValueDictionary()


    def disconnect(self):
        """Disconnects the client websocket.

        Does nothing if the client is not currently connected.
        """

        # Make local copies to avoid race conditions
        websocket = self._websocket
        self._websocket = None

        # Perform the actual disconnect
        if websocket:
            websocket.close()

        # Tell all the subscriptions that we've disconnected
        for queue in self._notify_queues.values():
            queue.put(StopIteration())

        self._notify_queues = {}

        # Tell all the waiting parties that we've disconnected
        with self._async_result_available:
            self._async_results = {}
            self._async_result_available.notify_all()


    def connect(self, force=False):
        """Connects the client websocket
        
        Does nothing if the client is currently connected, unless force is 
        specified.

        Args:
            force: if True, any existing connection will be disconnected first
        """
        if force:
            self.disconnect()
        elif self._websocket:
            # Already connected.
            return

        parsed = urlparse(self.url)
        if parsed.scheme == 'https':
            parsed = parsed._replace(scheme='wss')
        else:
            parsed = parsed._replace(scheme='ws')
        ws_url = urljoin(urlunparse(parsed), '/ws/api/v1/')

        # Connect the websocket
        self._websocket = websocket.create_connection(
            ws_url,
            sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1), )
            )

        # Start background thread
        thread = threading.Thread(target=self._ws_loop, 
                                  args=(self._websocket,))
        thread.daemon = True
        thread.start()
        

    def _ws_loop(self, websocket):
        try:
            while websocket == self._websocket:
                msg = websocket.recv()
                self._ws_message(msg)
        finally:
            self.disconnect()

    def _ws_message(self, msg):
        """Handle a single websocket message"""
        msg = json.loads(msg)

        if msg.get('message') == 'test_request':
            self._request('/api/v1/public/ping', _no_wait=True)
            return

        msg_id = msg.get('id')
        if msg_id in self._async_results:
            self._async_results[msg_id] = msg
            with self._async_result_available:
                self._async_result_available.notify_all()
        

        for notification in msg.pop('notifications', ''):
            self._process_notification(notification['message'], 
                                       notification['result'])

    def _process_notification(self, message, notifications):
        if not isinstance(notifications, list):
            # order_book events is not wrapped in a list.
            notifications = [notifications]

        for notification in notifications:
            queues = self._notify_queues.get((message, None), [])
            for subscriber in queues:
                subscriber.put(notification)

            instrument = notification.get('instrument')
            if instrument:
                queues = self._notify_queues.get((message, instrument), [])
                for subscriber in queues:
                    subscriber.put(notification)

    def _generate_serial(self) -> str:
        return "".join(
            random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                          "abcdefghijklmnopqrstuvwxyz"
                          "0123456789") for _ in range(10))

    def request(self, action, data=None, _no_wait=False):
        if not self._websocket:
            raise ValueError("%s is not connected." % type(self).__name__)

        data = {k: v for (k, v) in data.items() if v is not None}

        serial = self._generate_serial()

        msg = {
            'id': serial,
            'action': action,
            'arguments': data,
        }

        if self.key and self.secret:
            # Always sign if possible
            msg['sig'] = signature = self.generate_signature(action, data)
        elif action.startswith('/api/v1/private'):
            # couldn't sign, but signature is required
            raise ValueError("Key or secret empty")

        if not _no_wait:
            self._async_results[serial] = _pending

        self._websocket.send(json.dumps(msg))
        if _no_wait:
            return

        try:
            while self._async_results[serial] is _pending:
                with self._async_result_available:
                    self._async_result_available.wait()
        except KeyError:  # When we disconnect, async_results is cleared
            raise DeribitDisconnected()

        response_data = self._async_results.pop(serial)
        return self._interpret_response(response_data)


    @staticmethod
    def _queue_iterator(the_queue):
        while True:
            item = the_queue.get(block=True)
            if isinstance(item, Exception):
                raise item
            yield item

    def _generic_subscribe(self, event, instrument=None, channel=None):
        """Subscribe to some stream of events.

        Args:
            event: the event name to subscribe to.
            instrument: the instrument for which to subscribe
        """
        channel = channel or event + '_event'
        event_key = (channel, instrument)

        queue_list = self._notify_queues.get(event_key)
        if not queue_list:
            queue_list = self._notify_queues.setdefault(event_key,
                                                        weakref.WeakSet())

        # Only subscribe on the first client
        need_subscribe = len(queue_list) == 0

        result = queue.Queue()
        queue_list.add(result)

        if need_subscribe:
            self.request('/api/v1/private/subscribe', {
                'event': [event],
                'instrument': [instrument or 'all'],
                'continue': True
            })
        
        return self._queue_iterator(result)


    def subscribe_trades(self, instrument):
        """Subscribe to trades for the specified instrument."""
        return self._generic_subscribe('trade', instrument)


    def subscribe_my_trades(self, instrument=None):
        """Subscribe to user trades."""
        return self._generic_subscribe('my_trade', instrument)


    def subscribe_orders(self, instrument=None):
        """Subscribe to order changes."""
        return self._generic_subscribe('user_order', instrument,
                                       channel='user_orders_event')

    def subscribe_portfolio(self):
        """Subscribe to portfolio changes."""
        return self._generic_subscribe('portfolio')


    def subscribe_orderbook(self, instrument):
        """Subscribe to orderbooks for the specified instrument."""
        return self._generic_subscribe('order_book', instrument)


    def setheartbeat(self, interval):
        """Set the heartbeat.
        
        The heartbeat is used to check if the API is still responding."""
        if interval:
            self.request('/api/v1/public/setheartbeat', {'interval': interval})
        else:
            self.request('/api/v1/public/cancelheartbeat', {})
        self._websocket.timeout = interval


    def cancelondisconnect(self, state=True):
        """Set up cancel on disconnect."""
        self.request('/api/v1/private/cancelondisconnect', {'state': state})
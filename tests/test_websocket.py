import datetime
import os
import time

import pytest

from deribit_api import WebsocketClient, RestClient

# assumed price range for BTC
BTC_MIN_PRICE = 60.
BTC_MAX_PRICE = 60000.

###############################################################################
# Pytest fixture

def _close_positions(client):
    client.cancelall()

    positions = client.positions()

    if positions:
        for position in positions:
            if position["size"] > 0:
                client.sell(
                    position["instrument"],
                    position["size"],
                    price=round(0.8 * btc_price()),
                )
            else:
                client.buy(
                    position["instrument"],
                    -position["size"],
                    price=round(1.2 * btc_price()),
                )

_client = None

@pytest.fixture
def client():
    """Provide a clean client to the unit test

    This fixture makes sure the tests depending on it will use a clean client.
    A clean client will use an account that does not have any open positions or
    orders. After the test is completed, all remaining positions and orders
    will be closed.
    """
    global _client
    try:
        key = os.environ["DERIBIT_KEY"]
        secret = os.environ["DERIBIT_SECRET"]
    except KeyError:
        pytest.skip("Need DERIBIT_KEY and DERIBIT_SECRET in the environment")

    if  not _client:
        _client = WebsocketClient(key=key, secret=secret, 
                                  url="https://test.deribit.com")
        _client.connect()


    _close_positions(_client)
    yield _client  # Tests are run here
    _close_positions(_client)


@pytest.fixture(scope="module")
def btc_price():
    client = RestClient(url="https://test.deribit.com")
    return client.getsummary("BTC-PERPETUAL")["markPrice"]


###############################################################################
# Subscriptions

def test_orderbook(client, btc_price):
    subscription = client.subscribe_orderbook("BTC-PERPETUAL")

    ob = next(subscription)
    ts0 = ob['tstamp']

    # Force the orderbook to change by placing a market order
    client.buy("BTC-PERPETUAL", 10, round(1.2 * btc_price))

    ob = next(subscription)

    assert ob['tstamp'] > ts0


def test_trades(client, btc_price):
    trade_sub = client.subscribe_trades("BTC-PERPETUAL")

    # Force a trade by placing a market order
    client.buy("BTC-PERPETUAL", 2, round(1.2 * btc_price))

    t0 = time.time()
    trade = next(trade_sub)

    assert time.time() - t0 < 1

    assert isinstance(trade['tradeId'], int)
    assert trade['instrument'] == "BTC-PERPETUAL"
    assert isinstance(trade['tradeSeq'], int)
    assert isinstance(trade['timeStamp'], int)
    assert abs(trade['timeStamp'] / 1000 - time.time()) < 10 
    assert isinstance(trade['quantity'], int)
    assert BTC_MIN_PRICE < trade['price'] < BTC_MAX_PRICE
    assert trade['direction'] in ["buy", "sell"]
    assert trade['tickDirection'] in [0, 1, 2, 3]


def test_my_trades(client, btc_price):
    trade_sub = client.subscribe_my_trades()

    # Force a trade by placing a market order
    client.buy("BTC-PERPETUAL", 10, round(1.2 * btc_price))

    t0 = time.time()
    trade = next(trade_sub)

    assert time.time() - t0 < 1

    assert isinstance(trade['tradeId'], int)
    assert trade['instrument'] == "BTC-PERPETUAL"
    assert isinstance(trade['tradeSeq'], int)
    assert isinstance(trade['timeStamp'], int)
    assert abs(trade['timeStamp'] / 1000 - time.time()) < 10 
    assert isinstance(trade['quantity'], int)
    assert BTC_MIN_PRICE < trade['price'] < BTC_MAX_PRICE
    assert trade['direction'] in ["buy", "sell"]
    assert trade['tickDirection'] in [0, 1, 2, 3]


def test_my_orders(client, btc_price):
    order_sub = client.subscribe_orders()

    # Force a order by placing a market order
    br = client.buy("BTC-PERPETUAL", 3, round(0.8 * btc_price))

    t0 = time.time()
    order = next(order_sub)

    assert time.time() - t0 < 1
    assert (order['created'] - time.time()) < 10
    assert order['lastUpdate'] >= order['created']

    assert isinstance(order['orderId'], int)
    assert order['orderId'] == br['order']['orderId']
    assert order['instrument'] == "BTC-PERPETUAL"
    assert order['direction'] == "buy"
    assert order['price'] == price
    assert order['label'] == ""
    assert order['quantity'] == 3
    assert order['filledQuantity'] == 0.0
    assert order['state'] == "open"

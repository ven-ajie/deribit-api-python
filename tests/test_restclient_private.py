import datetime
import os
import time

import pytest

from deribit_api import RestClient

# assumed price range for BTC
BTC_MIN_PRICE = 60.
BTC_MAX_PRICE = 60000.


###############################################################################
# Pytest fixtures


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


@pytest.fixture
def client():
    """Provide a clean client to the unit test

    This fixture makes sure the tests depending on it will use a clean client.
    A clean client will use an account that does not have any open positions or
    orders. After the test is completed, all remaining positions and orders
    will be closed.
    """
    try:
        key = os.environ["DERIBIT_KEY"]
        secret = os.environ["DERIBIT_SECRET"]
    except KeyError:
        pytest.skip("Need DERIBIT_KEY and DERIBIT_SECRET in the environment")

    client = RestClient(key=key, secret=secret, url="https://test.deribit.com")

    _close_positions(client)
    yield client  # Tests are run here
    _close_positions(client)


@pytest.fixture(scope="module")
def btc_price():
    client = RestClient(url="https://test.deribit.com")
    return client.getsummary("BTC-PERPETUAL")["markPrice"]


###############################################################################
# Actual tests


def test_get_account(client, btc_price):
    account = client.account()

    assert isinstance(account["equity"], float)
    assert isinstance(account["maintenanceMargin"], float)
    assert isinstance(account["initialMargin"], float)
    assert account["maintenanceMargin"] == 0.0
    assert account["initialMargin"] == 0.0
    assert isinstance(account["availableFunds"], float)
    assert isinstance(account["balance"], float)
    assert account["availableFunds"] <= account["balance"]
    # Verify deposit is a btc address
    print(account["depositAddress"])
    assert 25 <= len(account["depositAddress"]) <= 34
    base58 = "abcdefghjklmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ123456789"
    assert all(c in base58 for c in account["depositAddress"])
    assert isinstance(account["SUPL"], float)
    assert isinstance(account["SRPL"], float)
    assert isinstance(account["PNL"], float)
    assert isinstance(account["optionsPNL"], float)
    assert isinstance(account["optionsSUPL"], float)
    assert isinstance(account["optionsSRPL"], float)
    assert isinstance(account["optionsD"], float)
    assert account["optionsD"] == 0.0
    assert isinstance(account["optionsG"], float)
    assert isinstance(account["optionsV"], float)
    assert isinstance(account["optionsTh"], float)
    assert isinstance(account["futuresPNL"], float)
    assert isinstance(account["futuresSUPL"], float)
    assert isinstance(account["futuresSRPL"], float)
    assert isinstance(account["deltaTotal"], float)
    assert account["deltaTotal"] == 0

    client.buy("BTC-PERPETUAL", 2, round(1.2 * btc_price))
    account2 = client.account()
    assert account2["maintenanceMargin"] > 0.0
    assert account2["initialMargin"] > 0.0
    assert account2["deltaTotal"] > 0.0
    assert account2["availableFunds"] < account["availableFunds"]
    assert account2["balance"] < account["balance"]


def test_buy(client, btc_price):
    response = client.buy(
        "BTC-PERPETUAL", 2, round(.8 * btc_price), True, "test_buy"
    )

    assert (response["order"]["created"] / 1000 - time.time()) < 10
    assert (response["order"]["lastUpdate"] / 1000 - time.time()) < 10
    assert isinstance(response["order"]["orderId"], int)
    assert response["order"]["instrument"] == "BTC-PERPETUAL"
    assert response["order"]["direction"] == "buy"
    assert isinstance(response["order"]["price"], float)
    assert response["order"]["label"] == "test_buy"
    assert response["order"]["quantity"] == 2.0
    assert response["order"]["filledQuantity"] == 0.0
    assert isinstance(response["order"]["avgPrice"], float)  # TODO: checkrange
    assert isinstance(response["order"]["commission"], float)
    assert response["order"]["state"] == "open"
    # assert response['order']['postOnly'] is True # Broken as of 2018-08-29
    assert response["order"]["api"] is True
    assert response["order"]["max_show"] == 2.0
    assert response["order"]["adv"] is False

    assert len(response["trades"]) == 0


def test_buy2(client, btc_price):
    # Like test_buy, but with a market order, and named parameters
    #    def buy(self, instrument, quantity, price, postOnly=None, label=None):

    response = client.buy(
        instrument="BTC-PERPETUAL",
        quantity=1,
        price=round(1.2 * btc_price),
        postOnly=False,
        label="test_buy2",
    )

    assert (response["order"]["created"] / 1000 - time.time()) < 10
    assert (response["order"]["lastUpdate"] / 1000 - time.time()) < 10
    assert isinstance(response["order"]["orderId"], int)
    assert response["order"]["instrument"] == "BTC-PERPETUAL"
    assert response["order"]["direction"] == "buy"
    assert isinstance(response["order"]["price"], float)
    assert response["order"]["label"] == "test_buy2"
    assert response["order"]["quantity"] == 1.0
    assert response["order"]["filledQuantity"] == 1
    assert isinstance(response["order"]["avgPrice"], float)
    assert isinstance(response["order"]["commission"], float)
    assert response["order"]["state"] == "filled"
    assert response["order"]["postOnly"] is False
    assert response["order"]["api"] is True
    assert response["order"]["max_show"] == 1.0
    assert response["order"]["adv"] is False

    assert len(response["trades"]) >= 1

    for trade in response["trades"]:
        assert trade["label"] == "test_buy2"
        assert trade["selfTrade"] == 0
        assert isinstance(trade["amount"], (int, float))
        assert isinstance(trade["quantity"], (int, float))
        assert isinstance(trade["price"], float)
        assert isinstance(trade["tradeSeq"], int)
        assert isinstance(trade["matchingId"], int)


def test_sell(client, btc_price):
    response = client.sell(
        "BTC-PERPETUAL", 1, round(1.2 * btc_price), True, "testlabel"
    )

    assert (response["order"]["created"] / 1000 - time.time()) < 10
    assert (response["order"]["lastUpdate"] / 1000 - time.time()) < 10
    assert isinstance(response["order"]["orderId"], int)
    assert response["order"]["instrument"] == "BTC-PERPETUAL"
    assert response["order"]["direction"] == "sell"
    assert isinstance(response["order"]["price"], float)
    assert response["order"]["label"] == "testlabel"
    assert response["order"]["quantity"] == 1.0
    assert response["order"]["filledQuantity"] == 0.0
    assert BTC_MIN_PRICE < response["order"]["avgPrice"] < BTC_MAX_PRICE
    assert isinstance(response["order"]["commission"], float)
    assert response["order"]["state"] == "open"
    # assert response['order']['postOnly'] is True # Broken as of 2018-08-29
    assert response["order"]["api"] is True
    assert response["order"]["max_show"] == 1.0
    assert response["order"]["adv"] is False

    assert len(response["trades"]) == 0


def test_sell2(client, btc_price):
    # Like test_sell, but with a market order, and named parameters

    response = client.sell(
        instrument="BTC-PERPETUAL",
        quantity=1,
        price=round(.8 * btc_price),
        postOnly=False,
        label="test_sell2",
    )

    assert (response["order"]["created"] / 1000 - time.time()) < 10
    assert (response["order"]["lastUpdate"] / 1000 - time.time()) < 10
    assert isinstance(response["order"]["orderId"], int)
    assert response["order"]["instrument"] == "BTC-PERPETUAL"
    assert response["order"]["direction"] == "sell"
    assert isinstance(response["order"]["price"], float)
    assert response["order"]["label"] == "test_sell2"
    assert response["order"]["quantity"] == 1.0
    assert response["order"]["filledQuantity"] == 1
    assert isinstance(response["order"]["avgPrice"], float)
    assert isinstance(response["order"]["commission"], float)
    assert response["order"]["state"] == "filled"
    assert response["order"]["postOnly"] is False
    assert response["order"]["api"] is True
    assert response["order"]["max_show"] == 1.0
    assert response["order"]["adv"] is False

    assert len(response["trades"]) >= 1

    for trade in response["trades"]:
        assert trade["label"] == "test_sell2"
        assert trade["selfTrade"] == 0
        assert isinstance(trade["amount"], (int, float))
        assert isinstance(trade["quantity"], (int, float))
        assert isinstance(trade["price"], float)
        assert isinstance(trade["tradeSeq"], int)
        assert isinstance(trade["matchingId"], int)


def test_edit(client, btc_price):
    response = client.buy("BTC-PERPETUAL", 5, round(.8 * btc_price))
    response = client.edit(
        response["order"]["orderId"], 3, round(.8 * btc_price)
    )

    assert (response["order"]["created"] / 1000 - time.time()) < 10
    assert response["order"]["lastUpdate"] > response["order"]["created"]
    assert isinstance(response["order"]["orderId"], int)
    assert response["order"]["instrument"] == "BTC-PERPETUAL"
    assert response["order"]["direction"] == "buy"
    assert isinstance(response["order"]["price"], float)
    assert response["order"]["label"] == ""
    assert response["order"]["quantity"] == 3
    assert response["order"]["filledQuantity"] == 0.0
    assert isinstance(response["order"]["avgPrice"], float)  # TODO: checkrange
    assert isinstance(response["order"]["commission"], float)
    assert response["order"]["state"] == "open"
    assert response["order"]["postOnly"] is False
    assert response["order"]["api"] is True
    assert response["order"]["max_show"] == 3
    assert response["order"]["adv"] is False

    assert len(response["trades"]) == 0

    response = client.edit(
        orderId=response["order"]["orderId"],
        quantity=15,
        price=round(.8 * btc_price),
    )
    assert response["order"]["quantity"] == 15


def test_cancel(client, btc_price):
    client.buy("BTC-PERPETUAL", 2, price=round(.8 * btc_price))
    order2 = client.buy("BTC-PERPETUAL", 3, price=round(.8 * btc_price))[
        "order"
    ]

    cancelled_order = client.cancel(order2["orderId"])
    assert cancelled_order["order"]["state"] == "cancelled"

    assert len(client.getopenorders()) == 1


def test_cancel_all(client, btc_price):
    client.buy("BTC-PERPETUAL", 2, price=round(0.8 * btc_price))
    client.buy("BTC-PERPETUAL", 3, price=round(0.8 * btc_price))

    assert len(client.getopenorders()) == 2

    result = client.cancelall("options")
    assert result == "cancel all options"

    assert len(client.getopenorders()) == 2

    result = client.cancelall(typeDef="futures")
    assert result == "cancel all futures"

    assert len(client.getopenorders()) == 0


def test_getopenorders(client, btc_price):
    open_orders = client.getopenorders()
    assert len(open_orders) == 0

    order = client.buy("BTC-PERPETUAL", 10, price=round(0.8 * btc_price))[
        "order"
    ]

    open_orders = client.getopenorders("options")
    assert len(open_orders) == 0

    open_orders = client.getopenorders(instrument="futures")
    assert len(open_orders) == 1
    assert open_orders[0] == order

    open_orders = client.getopenorders(instrument="BTC-PERPETUAL")
    assert len(open_orders) == 1
    assert open_orders[0] == order

    price = round(0.8 * client.getsummary("BTC-PERPETUAL")["markPrice"])
    order = client.buy("BTC-PERPETUAL", 15, price=price)["order"]

    open_orders = client.getopenorders(orderId=order["orderId"])
    assert len(open_orders) == 1
    assert open_orders[0] == order


def test_get_positions(client, btc_price):

    positions = client.positions()
    assert len(positions) == 0

    client.buy("BTC-PERPETUAL", 10, price=round(1.2 * btc_price))

    positions = client.positions()
    assert len(positions) == 1
    pos = positions[0]

    assert pos["instrument"] == "BTC-PERPETUAL"
    assert pos["kind"] == "future"
    assert pos["size"] == 10
    assert isinstance(pos["averagePrice"], float)
    assert BTC_MIN_PRICE < pos["averagePrice"] < BTC_MAX_PRICE
    assert pos["direction"] == "buy"
    assert isinstance(pos["sizeBtc"], float)
    assert isinstance(pos["floatingPl"], float)
    assert isinstance(pos["realizedPl"], float)
    assert isinstance(pos["estLiqPrice"], float)
    assert isinstance(pos["markPrice"], float)
    assert isinstance(pos["indexPrice"], float)
    assert isinstance(pos["maintenanceMargin"], float)
    assert isinstance(pos["initialMargin"], float)
    assert isinstance(pos["settlementPrice"], float)
    assert isinstance(pos["delta"], float)
    assert isinstance(pos["openOrderMargin"], float)
    assert isinstance(pos["profitLoss"], float)


def test_get_order_history(client, btc_price):
    # Do 3 trades to make sure there's something in our trade history
    client.buy("BTC-PERPETUAL", 10, price=round(1.2 * btc_price))
    client.sell("BTC-PERPETUAL", 10, price=round(0.8 * btc_price))
    order = client.buy("BTC-PERPETUAL", 10, price=round(1.2 * btc_price))[
        "order"
    ]

    order_history = client.orderhistory(count=1)
    assert len(order_history) == 1
    assert order_history[0]["orderId"] == order["orderId"]

    order_history = client.orderhistory(2)
    assert len(order_history) == 2

    order_history = client.orderhistory()
    assert len(order_history) >= 3


def test_get_my_trades(client, btc_price):
    start_trade_id = client.tradehistory()[0]["tradeId"]

    order = client.buy("BTC-PERPETUAL", 3, price=round(0.8 * btc_price))[
        "order"
    ]
    my_trades = client.tradehistory(10, "all")
    assert len(my_trades) >= 1

    for trade in my_trades:
        assert isinstance(trade["tradeId"], int)
        assert trade["instrument"] == "BTC-PERPETUAL"
        assert isinstance(trade["tradeSeq"], int)
        assert BTC_MIN_PRICE < trade["price"] < BTC_MAX_PRICE
        assert not trade["matchingId"]
        assert isinstance(trade["tickDirection"], int)
        assert isinstance(trade["fee"], float)
        assert BTC_MIN_PRICE < trade["indexPrice"] < BTC_MAX_PRICE
        assert trade["selfTrade"] is False

        if trade["tradeId"] > start_trade_id:
            assert trade["orderId"] == order["orderId"]
            assert abs(trade["timeStamp"] - time.time()) < 10
            assert trade["side"] == "buy"
            assert trade["liquidity"] == "T"
            assert trade["fee"] > 0
            assert trade["fee_currency"] == "BTC"

    my_trades = client.tradehistory(
        countNum=10, instrument="all", startTradeId=start_trade_id
    )

    assert not any(t["tradeId"] >= start_trade_id for t in my_trades)

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


@pytest.fixture
def anonymous_client(request):
    """Provide a anonymous_client to the unit test."""

    yield RestClient(url="https://test.deribit.com")


@pytest.fixture(scope="module")
def btc_price(request):
    client = RestClient(url="https://test.deribit.com")
    return client.getsummary("BTC-PERPETUAL")["markPrice"]


###############################################################################
# Public methods


def test_get_orderbook(anonymous_client):
    orderbook = anonymous_client.getorderbook("BTC-PERPETUAL")
    assert orderbook["instrument"] == "BTC-PERPETUAL"

    orderbook = anonymous_client.getorderbook(instrument="BTC-PERPETUAL")
    assert orderbook["instrument"] == "BTC-PERPETUAL"
    assert orderbook["state"] == "open"

    # Check the range of the prices
    assert BTC_MIN_PRICE < orderbook["settlementPrice"]
    assert orderbook["settlementPrice"] < BTC_MAX_PRICE
    assert BTC_MIN_PRICE < orderbook["min"] < orderbook["max"] < BTC_MAX_PRICE
    assert BTC_MIN_PRICE < orderbook["low"] < orderbook["high"] < BTC_MAX_PRICE
    assert BTC_MIN_PRICE < orderbook["last"] < BTC_MAX_PRICE
    assert BTC_MIN_PRICE < orderbook["mark"] < BTC_MAX_PRICE
    assert orderbook["low"] <= orderbook["last"] <= orderbook["high"]
    assert orderbook["min"] <= orderbook["mark"] <= orderbook["max"]

    assert abs(orderbook["tstamp"] / 1000 - time.time()) < 10

    assert all(
        b1["price"] > b2["price"]
        for (b1, b2) in zip(orderbook["bids"], orderbook["bids"][1:])
    )
    assert all(
        a1["price"] < a2["price"]
        for (a1, a2) in zip(orderbook["asks"], orderbook["asks"][1:])
    )
    assert all(
        b1["cm"] <= b2["cm"]
        for (b1, b2) in zip(orderbook["bids"], orderbook["bids"][1:])
    )
    assert all(
        a1["cm"] <= a2["cm"]
        for (a1, a2) in zip(orderbook["asks"], orderbook["asks"][1:])
    )


def test_get_instruments(anonymous_client):
    instruments = anonymous_client.getinstruments()

    now = datetime.datetime.now()

    # Check stuff that's true for all futures
    for instrument in instruments:
        assert instrument["isActive"] is True
        assert isinstance(instrument["minTradeSize"], (float, int))

        assert instrument["created"].endswith(" GMT")
        parsed = datetime.datetime.strptime(
            instrument["created"][:-4], "%Y-%m-%d %H:%M:%S"
        )
        assert parsed < now

        assert instrument["tickSize"] > 0.0
        assert instrument["pricePrecision"] > 0.0
        assert instrument["expiration"].endswith(" GMT")
        parsed = datetime.datetime.strptime(
            instrument["expiration"][:-4], "%Y-%m-%d %H:%M:%S"
        )
        assert isinstance(instrument["minTradeSize"], (float, int))
        assert parsed > now

    futures = [i for i in instruments if i["kind"] == "future"]
    for instrument in futures:

        # check the perpetual
        if instrument["instrumentName"] == "BTC-PERPETUAL":
            assert instrument["baseCurrency"] == "BTC"
            assert instrument["currency"] == "USD"
            assert instrument["settlement"] == "perpetual"
            assert instrument["expiration"] == "3000-01-01 08:00:00 GMT"

    # Check stuff that's supposed to be true for all options
    options = [i for i in instruments if i["kind"] == "option"]
    for instrument in options:
        assert instrument["strike"] > 0
        assert instrument["optionType"] in ["call", "put"]
        assert instrument["isActive"] is True
        assert isinstance(instrument["minTradeSize"], (float, int))


def test_get_currencies(anonymous_client):
    currencies = anonymous_client.getcurrencies()
    for currency in currencies:
        assert 3 <= len(currency["currency"]) <= 7
        assert currency["currencyLong"]
        assert isinstance(currency["minConfirmation"], int)
        assert currency["minConfirmation"] >= 1
        assert currency["txFee"] >= 0
        assert currency["isActive"] is True
        assert currency["coinType"] == "BITCOIN"


def test_get_trades(anonymous_client):
    trades = anonymous_client.getlasttrades("BTC-PERPETUAL", 102)

    assert len(trades) == 102

    for trade in trades:
        assert isinstance(trade["tradeId"], int)
        assert trade["instrument"] == "BTC-PERPETUAL"
        assert isinstance(trade["tradeSeq"], int)
        assert isinstance(trade["timeStamp"], int)
        assert isinstance(trade["quantity"], int)
        assert BTC_MIN_PRICE < trade["price"] < BTC_MAX_PRICE
        assert trade["direction"] in ["buy", "sell"]
        assert trade["tickDirection"] in [0, 1, 2, 3]

    trade_id = trades[1]["tradeId"]

    # Check the edge behaviour of since (it is not inclusive)
    trades = anonymous_client.getlasttrades("BTC-PERPETUAL", 4, trade_id - 1)
    assert any(t["tradeId"] == trade_id for t in trades)

    trades = anonymous_client.getlasttrades(
        instrument="BTC-PERPETUAL", count=4, since=trade_id
    )
    assert not any(t["tradeId"] == trade_id for t in trades)


def test_get_summary(anonymous_client):
    summary = anonymous_client.getsummary("BTC-PERPETUAL")
    assert summary["instrumentName"] == "BTC-PERPETUAL"

    summary = anonymous_client.getsummary(instrument="BTC-PERPETUAL")
    assert isinstance(summary["funding8h"], float)
    assert isinstance(summary["currentFunding"], float)
    assert summary["instrumentName"] == "BTC-PERPETUAL"
    assert summary["openInterest"] > 0
    assert BTC_MIN_PRICE < summary["low"] < summary["high"] < BTC_MAX_PRICE
    assert summary["volume"] > 0
    assert summary["volumeBtc"] > 0
    assert BTC_MIN_PRICE < summary["last"] < BTC_MAX_PRICE
    assert BTC_MIN_PRICE < summary["bidPrice"] < BTC_MAX_PRICE
    assert BTC_MIN_PRICE < summary["askPrice"] < BTC_MAX_PRICE
    assert BTC_MIN_PRICE < summary["midPrice"] < BTC_MAX_PRICE
    assert BTC_MIN_PRICE < summary["estDelPrice"] < BTC_MAX_PRICE
    assert BTC_MIN_PRICE < summary["markPrice"] < BTC_MAX_PRICE

    assert summary["created"].endswith(" GMT")
    parsed = datetime.datetime.strptime(
        summary["created"][:-4], "%Y-%m-%d %H:%M:%S"
    )
    assert parsed < datetime.datetime.now()


def test_get_index(anonymous_client):
    index = anonymous_client.index()

    assert BTC_MIN_PRICE < index["btc"] < BTC_MAX_PRICE
    assert BTC_MIN_PRICE < index["edp"] < BTC_MAX_PRICE


def test_get_stats(anonymous_client):
    stats = anonymous_client.stats()

    assert stats["created"].endswith(" GMT")
    parsed = datetime.datetime.strptime(
        stats["created"][:-4], "%Y-%m-%d %H:%M:%S"
    )
    assert parsed < datetime.datetime.now()

    assert stats["btc_usd"]["futuresVolume"] > 0
    assert stats["btc_usd"]["putsVolume"] > 0
    assert stats["btc_usd"]["callsVolume"] > 0


def test_cant_do_private(anonymous_client):
    with pytest.raises(Exception) as excinfo:
        anonymous_client.buy('BTC-PERPETUAL', 10, 10000)

    assert 'key' in str(excinfo.value).lower()
    assert 'secret' in str(excinfo.value)

def test_invalid_request(anonymous_client):
    with pytest.raises(Exception) as excinfo:
        anonymous_client.request('/api/v1/not_a_valid_thing', {})

    assert 'bad_request' in str(excinfo.value)

def test_404(anonymous_client):
    with pytest.raises(Exception) as excinfo:
        anonymous_client.request('/not_api', {})

    assert 'Wrong response code' in str(excinfo.value)
        

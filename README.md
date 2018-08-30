# API Client for [Deribit API](https://www.deribit.com/docs/api/)

## Description

The [Deribit API](https://www.deribit.com) is available in this package.

### Installation

```
sudo pip install deribit-api

```

### Example

```
from deribit_api import RestClient
client = RestClient("KEY", "SECRET")
client.index()
client.account()
```

## API - REST Client

`RestClient(key, secret, url)`

Constructor creates new REST client.

**Parameters**

| Name     | Type     | Decription                                                |
|----------|----------|-----------------------------------------------------------|
| `key`    | `string` | Optional, Access Key needed to access Private functions   |
| `secret` | `string` | Optional, Access Secret needed to access Private functions|
| `url`    | `string` | Optional, server URL, default: `https://www.deribit.com`  |


### Methods

* `getorderbook(instrument)` - [Doc](https://www.deribit.com/docs/api/#getinstruments), public

  Retrieve the orderbook for a given instrument.

  **Parameters**

  | Name         | Type       | Decription                                                 |
  |--------------|------------|------------------------------------------------------------|
  | `instrument` | `string`   | Required, instrument name                                  |

* `index()` - [Doc](https://www.deribit.com/docs/api/#index), public

  Get price index, BTC-USD rates.

* `getcurrencies()` - [Doc](https://www.deribit.com/docs/api/#getcurrencies), public

  Get all supported currencies.

* `getorderbook(instrument)` - [Doc](https://www.deribit.com/docs/api/#getorderbook), public

  Retrieve the orderbook for a given instrument.

  **Parameters**

  | Name         | Type       | Decription                                                 |
  |--------------|------------|------------------------------------------------------------|
  | `instrument` | `string`   | Required, instrument name                                  |

* `getlasttrades(instrument, count, since)` - [Doc](https://www.deribit.com/docs/api/#getlasttrades), public

  Retrieve the latest trades that have occured for a specific instrument.

  **Parameters**

  | Name         | Type       | Decription                                                                    |
  |--------------|------------|-------------------------------------------------------------------------------|
  | `instrument` | `string`   | Required, instrument name                                                     |
  | `count`      | `integer`  | Optional, count of trades returned (limitation: max. count is 100)            |
  | `since`      | `integer`  | Optional, “since” trade id, the server returns trades newer than that “since” |

* `getsummary(instrument)` - [Doc](https://www.deribit.com/docs/api/#getsummary), public

  Retrieve the summary info such as Open Interest, 24H Volume etc for a specific instrument.

  **Parameters**

  | Name         | Type       | Decription                                                 |
  |--------------|------------|------------------------------------------------------------|
  | `instrument` | `string`   | Required, instrument name                                  |

* `account()` - [Doc](https://www.deribit.com/docs/api/#account), Private

  Get user account summary.

* `buy(instrument, quantity, price, postOnly, label)` - [Doc](https://www.deribit.com/docs/api/#buy), private

  Place a buy order in an instrument.

  **Parameters**

  | Name         | Type       | Decription                                                                        |
  |--------------|------------|-----------------------------------------------------------------------------------|
  | `instrument` | `string`   | Required, instrument name                                                         |
  | `quantity`   | `integer`  | Required, quantity, in contracts ($10 per contract for futures, ฿1 — for options) |
  | `price`      | `float`    | Required, USD for futures, BTC for options                                        |
  | `postOnly`   | `boolean`  | Optional, if true then the order will be POST ONLY                                |
  | `label`      | `string`   | Optional, user defined maximum 4-char label for the order                         |

* `sell(instrument, quantity, price, postOnly, label)` - [Doc](https://www.deribit.com/docs/api/#sell), private

  Place a sell order in an instrument.

  **Parameters**

  | Name         | Type       | Decription                                                                        |
  |--------------|------------|-----------------------------------------------------------------------------------|
  | `instrument` | `string`   | Required, instrument name                                                         |
  | `quantity`   | `integer`  | Required, quantity, in contracts ($10 per contract for futures, ฿1 — for options) |
  | `price`      | `float`    | Required, USD for futures, BTC for options                                        |
  | `postOnly`   | `boolean`  | Optional, if true then the order will be POST ONLY                                |
  | `label`      | `string`   | Optional, user defined maximum 4-char label for the order                         |

* `edit(orderId, quantity, price)` - [Doc](https://www.deribit.com/docs/api/#edit)

  Edit price and/or quantity of the own order. (Authorization is required).

  **Parameters**

  | Name         | Type       | Decription                                                                        |
  |--------------|------------|-----------------------------------------------------------------------------------|
  | `orderId`    | `integer`  | Required, ID of the order returned by "sell" or "buy" request                     |
  | `quantity`   | `integer`  | Required, quantity, in contracts ($10 per contract for futures, ฿1 — for options) |
  | `price`      | `float`    | Required, USD for futures, BTC for options                                        |

* `cancel(orderId)` - [Doc](https://www.deribit.com/docs/api/#cancel), private

  Cancell own order by id.

  **Parameters**

  | Name         | Type       | Decription                                                                        |
  |--------------|------------|-----------------------------------------------------------------------------------|
  | `orderId`    | `integer`  | Required, ID of the order returned by "sell" or "buy" request                     |

* `cancelall(type)` - [Doc](https://www.deribit.com/docs/api/#cancelall)

  Cancel all own futures, or all options, or all.

  **Parameters**

  | Name         | Type       | Decription                                                                                    |
  |--------------|------------|-----------------------------------------------------------------------------------------------|
  | `type`       | `string`   | Optional, type of instruments to cancel, allowed: "all", "futures", "options", default: "all" |

* `getopenorders(instrument, orderId)` - [Doc](https://www.deribit.com/docs/api/#getopenorders), private

  Retrieve open orders.

  **Parameters**

  | Name         | Type       | Description                                                           |
  |--------------|------------|-----------------------------------------------------------------------|
  | `instrument` | `string`   | Optional, instrument name, use if want orders for specific instrument |
  | `orderId`    | `integer`  | Optional, order id                                                    |

* `positions()` - [Doc](https://www.deribit.com/docs/api/#positions), private

  Retreive positions.

* `orderhistory(count)` - [Doc](https://www.deribit.com/docs/api/#orderhistory), private

  Get history.

  **Parameters**

  | Name       | Type       | Description                                                |
  |------------|------------|------------------------------------------------------------|
  | `count`    | `integer`  | Optional, number of requested records                      |

* `tradehistory(count, instrument, startTradeId)` - [Doc](https://www.deribit.com/docs/api/#tradehistory), private

  Get private trade history of the account. (Authorization is required). The result is ordered by trade identifiers (trade id-s).

  **Parameters**

  | Name           | Type       | Description                                                                                        |
  |----------------|------------|----------------------------------------------------------------------------------------------------|
  | `count`        | `integer`  | Optional, number of results to fetch. Default: 20                                                  |
  | `instrument`   | `string`   | Optional, name of instrument, also aliases “all”, “futures”, “options” are allowed. Default: "all" |
  | `startTradeId` | `integer`  | Optional, number of requested records                                                              |

## API - Websocket Client

The websocket client extends the restclient. All requests are sent over websocket for minumum delay. The websocket client also allows the user to subscribe to various event notifications.


* connect(self, force=False)

Connects the client to the websocket. Note that clients will need to connect before any other method is invoked. When `force` is true, any existing connection will be terminated first, otherwise connect will only connect when it is not already connected.

* disconnect(self)

Disconnects the client from the websocket. If the client is already disconnected, this does nothing.

* subscribe_trades(self, instrument) - [Doc](https://docs.deribit.com/rpc-notifications.html#tradeevent)

Subscribes to trades for the specified instrument. Returns an iterator, which can be used in for loops.

  **Parameters**

  | Name           | Type       | Description                                                                                        |
  |----------------|------------|----------------------------------------------------------------------------------------------------|
  | `instrument`   | `string`   | name of instrument   |

* subscribe_my_trades(self, instrument=None) - [Doc](https://docs.deribit.com/rpc-notifications.html#mytradeevent)

Subscribes to user trades. Returns an iterator, which can be used in for loops.

  **Parameters**

  | Name           | Type       | Description                                                                                        |
  |----------------|------------|----------------------------------------------------------------------------------------------------|
  | `instrument`   | `string`   | Optional, name of instrument to get user trades for. |

* subscribe_orders(self, instrument=None) - [Doc](https://docs.deribit.com/rpc-notifications.html#userorderevent)

Subscribes to changes in user's orders. Returns an iterator, which can be used in for loops.

  **Parameters**

  | Name           | Type       | Description                                                                                        |
  |----------------|------------|----------------------------------------------------------------------------------------------------|
  | `instrument`   | `string`   | Optional, name of instrument. |

* subscribe_portfolio(self) - [Doc](https://docs.deribit.com/rpc-notifications.html#portfolioevent)

Subscribes to changes in user's portfolio. Returns an iterator, which can be used in for loops.

* subscribe_orderbook(self, instrument) - [Doc](https://docs.deribit.com/rpc-notifications.html#orderbookevent)

Subscribes to changes in orderbook. Returns an iterator, which can be used in for loops.

  **Parameters**

  | Name           | Type       | Description                                                                                        |
  |----------------|------------|----------------------------------------------------------------------------------------------------|
  | `instrument`   | `string`   | name of instrument. |

* setheartbeat(self, interval)

Sets up heartbeats. A heartbeat checks on a specified interval to see if the connection is still function. If it isn't the connection is terminated. Especially useful in combination with cancelondisconnect

  | Name           | Type       | Description                                                                                        |
  |----------------|------------|----------------------------------------------------------------------------------------------------|
  | `interval`   | `int`   | The number of seconds between two hearbeats. |

* cancelondisconnect(self, state)

Sets up cancel on disconnect. When this is enabled, all user orders are cancelled when the websocket connection is lost.

  | Name           | Type       | Description                                                                                        |
  |----------------|------------|----------------------------------------------------------------------------------------------------|
  | `state`   | `bool` | Whether to enable cancelondisconnect |

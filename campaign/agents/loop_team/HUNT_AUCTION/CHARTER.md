# HUNT_AUCTION — Treasury auction demand (NEW tauctions.csv 7852 auctions) as risk regime, iter8

Premise: auction demand (bid-to-cover, indirect-direct skew) as a DAILY risk-on/off gate for
equity (SPY-class from twelve_big if present, else QQQ new) and/or as an event-avoid filter.
Data: tools/quant/data/treasury_auctions/tauctions.csv (2000+; Bill/Note/Bond; btc + direct/
indirect accepted 2010+). Build DAILY demand series: ffill each auction's btc/indirect share
forward (T+1 publish same-day evening -> trade next day), rolling 10-auction means.
Honesty: bt framework, 6.4bps, cap 1.6, all gates + scramble.
Last line: HUNT_AUCTION DONE

import talib

def initialize(context):
    set_symbol_lookup_date('2003-01-01')
    context.stocks = symbols('aapl','MSFT','nvda','amzn', 'intc')
    set_benchmark(symbol('qqq'))
    context.dayCount = 0
    context.date = None
    context.shorts = 0
    context.cancelCounter=0
    
def handle_data(context, data):  
    
    todays_date = get_datetime().date()
    
    if todays_date==context.date:
        return
    
    if todays_date!=context.date:
        context.dayCount+=1
        context.cancelCounter+=1
        context.date = todays_date
        
    if context.cancelCounter==5:
        end_of_day(context, data)
        context.cancelCounter=0
        
    if has_orders(context,data) and context.dayCount>1:
        print('has open orders - doing nothing!')
        return
    
    if context.dayCount == 1:
        buyAll(context,data)
    
    for stock in context.stocks:
        
        hist100 = history(bar_count=100, frequency='1d', field='price')
        series100 = hist100[stock]
        ema_result100 = talib.EMA(series100, timeperiod=100)
        ema_result50 = talib.EMA(series100, timeperiod=50)
        ema100 = ema_result100[-1]
        ema50 = ema_result50[-1]        
#            
        getCash(context,data)
#            
        if ema100 > ema50 and context.portfolio.positions[stock].amount > 0 and context.dayCount>2:
            log.info('{0}:  Selling {1} shares, EMA50:  {2}, EMA100:  {3}'.format(stock.symbol,context.portfolio.positions[stock].amount,ema50,ema100))
            order_target(stock, 0, style=LimitOrder(ema50))            
#        
        if has_orders(context,data) and context.dayCount>7:
            print('has open orders - doing nothing!')
            return
#            
        elif ema100 < ema50 and context.portfolio.positions[stock].amount == 0 and context.dayCount>2 and data[stock].price<context.freeCash:
            getCash(context,data)
            shares = round((context.freeCash*0.95)/data[stock].price,0)
            log.info('{0}:  Buying {1} shares, EMA50:  {2}, EMA100:  {3}'.format(stock.symbol,shares,ema50,ema100))
            order_target(stock, shares, style=LimitOrder(ema50))
#            
        getCash(context,data)
#            
        if context.portfolio.positions[stock].amount < 0:
            context.shorts+=1
#    
    getCash(context,data)        
    record(Cash=context.freeCash)
    record(Shorts=context.shorts)
    context.shorts=0   
        
def has_orders(context,data):
    # Return true if there are pending orders.
    has_orders = False
    for sec in data:
        orders = get_open_orders(sec)
        if orders:
            for oo in orders:                  
                message = 'Open order for {amount} shares in {stock}'  
                message = message.format(amount=oo.amount, stock=sec)  
                log.info(message)

            has_orders = True
    return has_orders
    
def getCash(context,data):
    if context.portfolio.cash < (context.portfolio.portfolio_value-context.portfolio.positions_value):
        context.freeCash = context.portfolio.cash
    else:
        context.freeCash = (context.portfolio.portfolio_value-context.portfolio.positions_value)
    
def end_of_day(context, data):
    #cancle any order at the end of day. Do it ourselves so we can see slow moving stocks.
    open_orders = get_open_orders()
    
    if open_orders:
        
        log.info("")
        log.info("* EOD: Stoping Orders *")
        log.info("")
    
    if open_orders:  
        
        for security, orders in open_orders.iteritems():
            for oo in orders:
                log.info("X CANCLED {0:s} with {1:,d} / {2:,d} filled"\
                                     .format(security.symbol,
                                             oo.filled,
                                             oo.amount))
                cancel_order(oo)

def buyAll(context,data):
    for stock in context.stocks:
        order_value(stock, 1000)
        log.info('{0}:  Buying {1}shares'.format(stock.symbol,round(1000/data[stock].price,0)))

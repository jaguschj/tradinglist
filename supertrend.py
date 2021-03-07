# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 08:03:21 2021

@author: JensJ
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

#from . import Indicator, Max, Min, MovAv, Atr

import backtrader as bt
from datetime import datetime
#from atr import AverageTrueRange
import backtrader.indicators as btind# import AverageTrueRange
import itertools

                            

class SuperTrendBand(bt.Indicator):
    """
    Helper inidcator for Supertrend indicator
    """
    params = (('period',7),('multiplier',3))
    lines = ('basic_ub','basic_lb','final_ub','final_lb')


    def __init__(self):
        self.atr = bt.indicators.AverageTrueRange(period=self.p.period)
        self.l.basic_ub = ((self.data.high + self.data.low) / 2) + (self.atr * self.p.multiplier)
        self.l.basic_lb = ((self.data.high + self.data.low) / 2) - (self.atr * self.p.multiplier)

    def next(self):
        if len(self)-1 == self.p.period:
            self.l.final_ub[0] = self.l.basic_ub[0]
            self.l.final_lb[0] = self.l.basic_lb[0]
        else:
            #=IF(OR(basic_ub<final_ub*,close*>final_ub*),basic_ub,final_ub*)
            if self.l.basic_ub[0] < self.l.final_ub[-1] or self.data.close[-1] > self.l.final_ub[-1]:
                self.l.final_ub[0] = self.l.basic_ub[0]
            else:
                self.l.final_ub[0] = self.l.final_ub[-1]

            #=IF(OR(baisc_lb > final_lb *, close * < final_lb *), basic_lb *, final_lb *)
            if self.l.basic_lb[0] > self.l.final_lb[-1] or self.data.close[-1] < self.l.final_lb[-1]:
                self.l.final_lb[0] = self.l.basic_lb[0]
            else:
                self.l.final_lb[0] = self.l.final_lb[-1]

                
                
class SuperTrend(bt.Indicator):
    """
    Super Trend indicator
    """
    params = (('period', 7), ('multiplier', 3))
    lines = ('super_trend',)
    plotinfo = dict(subplot=False)

    def __init__(self):
        self.stb = SuperTrendBand(period = self.p.period, multiplier = self.p.multiplier)

    def next(self):
        if len(self) - 1 == self.p.period:
            self.l.super_trend[0] = self.stb.final_ub[0]
            return

        if self.l.super_trend[-1] == self.stb.final_ub[-1]:
            if self.data.close[0] <= self.stb.final_ub[0]:
                self.l.super_trend[0] = self.stb.final_ub[0]
            else:
                self.l.super_trend[0] = self.stb.final_lb[0]

        if self.l.super_trend[-1] == self.stb.final_lb[-1]:
            if self.data.close[0] >= self.stb.final_lb[0]:
                self.l.super_trend[0] = self.stb.final_lb[0]
            else:
                self.l.super_trend[0] = self.stb.final_ub[0]
                

class SuperTrendStrategy(bt.Strategy):
    params = (('period', 7), ('multiplier', 3))
    
    opcounter = itertools.count(1)
 
    def __init__(self):
        self.supertrend = SuperTrend(self.data,multiplier=self.p.multiplier,period=self.p.period)  
        #self.supertrend = bt.ind.Supertrend(self.data)#,distdn=34,distup=55,period=13)  
        self.buysig = bt.ind.CrossUp (self.data,self.supertrend)
        self.sellsig = bt.ind.CrossDown (self.data,self.supertrend)
        # initial setting
        #self.up = self.supertrend.lines.sptup
        #self.dn = self.supertrend.lines.sptdn
        
    def log(self,txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))     
        
    # def notify_order(self, order):
        # if order.status == bt.Order.Completed:
            # t = ''
            # t += '{:02d}'.format(next(self.opcounter))
            # t += ' {}'.format(order.data.datetime.datetime().strftime('%y-%m-%d'))
            # t += ' BUY ' * order.isbuy() or ' SELL'
            # t += ' Size: {:+d} / Price: {:.2f}'
            # print(t.format(order.executed.size, order.executed.price))        

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # An active Buy/Sell order has been submitted/accepted - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED, {order.executed.price:.2f}')
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print(order)
            self.log('Order Canceled/Margin/Rejected')

        # Reset orders
        self.order = None      
            
    def next(self):
        if self.buysig > 0:
            self.order = self.buy()
            #self.log('Buy:  %.2f'%(self.datas[0].close[0]))
        if self.position:
            if self.sellsig > 0:
                self.order = self.close()
                #self.log('Sell: %.2f'%self.datas[0].close[0])
                #print(self.position)



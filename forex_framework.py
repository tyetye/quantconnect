# QUANTCONNECT.COM - Democratizing Finance, Empowering Individuals.
# Lean Algorithmic Trading Engine v2.0. Copyright 2014 QuantConnect Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
# This is a first attempt at a basic Forex framework for Quantconnect.com
# The goal is not to have a perfectly working algorithm but a base from which to start more complex algo engines.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from clr import AddReference
AddReference("System")
AddReference("QuantConnect.Algorithm")
AddReference("QuantConnect.Indicators")
AddReference("QuantConnect.Common")

from System import *
from QuantConnect import *
from QuantConnect.Data import *
from QuantConnect.Algorithm import *
from QuantConnect.Indicators import *

from System.Drawing import Color
from datetime import timedelta
import numpy as np


class BasicTemplateForexAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.Debug("\n\n ************ NEW SESSION **********\n")
        self.SetCash(1000)
        self.SetTimeZone("America/Chicago")
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2020, 1, 25)
        self.instrument = "EURJPY"
        self.AddForex(self.instrument, Resolution.Minute)
        
        self.fiveMinutePeriod  = 28
        self.sixtyMinutePeriod = 28
        self.emaSlowSixtyMinutePeriod     = 14
        self.emaFastSixtyMinutePeriod     = 5
        
        self.shortLong = 0   #this is a workaround because I can't get isLong/IsShort working at this moment (review later)
        
        self.fiveMinuteWindow = RollingWindow[QuoteBar](self.fiveMinutePeriod)
        self.Consolidate(self.instrument, timedelta(minutes=5), self.FiveMinuteQuoteHandler)

        self.sixtyMinuteWindow = RollingWindow[QuoteBar](self.sixtyMinutePeriod)
        self.Consolidate(self.instrument, timedelta(minutes=60), self.SixtyMinuteQuoteHandler)

        self.emaSlow = self.EMA(self.instrument, self.emaSlowSixtyMinutePeriod, Resolution.Hour)
        self.emaFast = self.EMA(self.instrument, self.emaFastSixtyMinutePeriod, Resolution.Hour)
        
        PriceChart = Chart("PriceChart")
        #PriceChart = Chart("PriceChart", ChartType.Stacked)
        PriceChart.AddSeries(Series("5 Minute", SeriesType.Line))
        PriceChart.AddSeries(Series("60 Minute", SeriesType.Line))
        PriceChart.AddSeries(Series("LONG", SeriesType.Scatter, "", Color.Yellow, ScatterMarkerSymbol.Triangle))
        PriceChart.AddSeries(Series("SHORT", SeriesType.Scatter, "", Color.Yellow, ScatterMarkerSymbol.TriangleDown))
        PriceChart.AddSeries(Series("LIQUIDATE", SeriesType.Scatter, "", Color.Yellow, ScatterMarkerSymbol.Circle))
        self.AddChart(PriceChart)
 
        IndicatorChart = Chart("IndicatorChart", ChartType.Stacked)
        IndicatorChart.AddSeries(Series("EMA Slow", SeriesType.Line))
        self.AddChart(IndicatorChart)
        
        self.PlotIndicator("EMA", self.emaSlow)
        self.PlotIndicator("EMA", self.emaFast)
        
    # This will run every five minutes on the collected 1min data
    def FiveMinuteQuoteHandler(self, consolidated):
        self.fiveMinuteWindow.Add(consolidated)
        #self.Debug(" 5 Window: " + str(self.fiveMinuteWindow[0].Close))
        self.Plot("PriceChart", "5 Minute", self.fiveMinuteWindow[0].Close)

 
    
    # This will run every sixty minutes on the collected 1min data
    def SixtyMinuteQuoteHandler(self, consolidated):
        self.sixtyMinuteWindow.Add(consolidated)
        #self.Debug("60 Window: \t\t" + str(self.sixtyMinuteWindow[0].Close))
        self.Plot("PriceChart", "60 Minute", self.sixtyMinuteWindow[0].Close)
  
     
    
    def OnData(self, data):
        if not self.Portfolio.Invested:
            if self.emaSlow < self.emaFast and self.shortLong == 0:
                self.SetHoldings(self.instrument, 1)
                self.shortLong = 1
                self.Debug("+ " + str(self.Time) + " OPEN LONG")
                self.Plot("PriceChart", "LONG", self.fiveMinuteWindow[0].Close)
            elif self.emaSlow > self.emaFast and self.shortLong == 0:
                self.SetHoldings(self.instrument, -1)
                self.shortLong = -1
                self.Debug("+ " + str(self.Time) + " OPEN SHORT")
                self.Plot("PriceChart", "SHORT", self.fiveMinuteWindow[0].Close)
                
        elif self.Portfolio.Invested:
            if self.shortLong==1 and self.emaFast < self.emaSlow:
                self.Liquidate(self.instrument)
                self.shortLong=0
                self.Debug("+ " + str(self.Time) + " LIQUIDATE LONG")
                self.Plot("PriceChart", "LIQUIDATE", self.fiveMinuteWindow[0].Close)
            elif self.shortLong==-1 and self.emaFast > self.emaSlow:
                self.Liquidate(self.instrument)
                self.shortLong=0
                self.Debug("+ " + str(self.Time) + " LIQUIDATE SHORT")
                self.Plot("PriceChart", "LIQUIDATE", self.fiveMinuteWindow[0].Close) 
        # Print to console to verify that data is coming in
        #self.Log(str(self.fiveMinuteWindow[0].Close))

#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Hackerfleet Technology Demonstrator
# =====================================================================
# Copyright (C) 2011-2014 riot <riot@hackerfleet.org> and others.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.



__author__ = 'riot'

from Kamaelia.File.WholeFileWriter import WholeFileWriter
from Kamaelia.File.Writing import SimpleFileWriter
from Kamaelia.File.Reading import SimpleReader
from Kamaelia.Util.Stringify import Stringify
from Kamaelia.Util.Collate import Collate
from Kamaelia.Chassis.Pipeline import Pipeline
from Kamaelia.Chassis.Graphline import Graphline
from Kamaelia.Util.Chooser import Chooser
from Kamaelia.Util.Clock import SimpleClock
from Kamaelia.Util.Console import ConsoleEchoer
from Kamaelia.Util.DataSource import DataSource, TriggeredSource
from Kamaelia.Util.Filter import Filter
from Kamaelia.Util.PureTransformer import PureTransformer
from Kamaelia.Util.Backplane import Backplane, PublishTo, SubscribeTo

from hfos.utils.serialport import SerialReader
from hfos.utils.httpgetter import HTTPGetter
from hfos.parsers.grib import GribParser
from hfos.utils.match import Match
from hfos.utils.dict import DictTemplater
from hfos.parsers.nmea import NMEAParser
from hfos.utils.templater import MakoTemplater

#from hfos.server.cherrypy import WebStore, WebGate
from hfos.utils.logger import log


def siteScraper(url, filterclass, decode=True):
    """Constructs a sitescraper containing a SimpleClock, TriggeredSource, HTTPGetter and Filter"""

    return Pipeline(TriggeredSource(url),
                    HTTPGetter(decode=decode),
                    Filter(filterclass)
    )


def siteDebugger(filename, filterclass):
    """Replacement function to not bother webpages you already downloaded
    for debugging purposes.
    Just replace
        siteScraper(url, ...
    with
        siteDebugger(path-to-dumped-file, ...
    (Leave the rest intact, less work and the filter is still required!)
    """

    return Pipeline(
        SimpleReader(filename),
        Collate(),
        Stringify(),
        Filter(filterclass)
    )


def fileDownloader(url, target, interval):
    """Constructs a filedownloader containing a SimpleClock, HTTPGetter and SimpleFileWriter"""

    return Pipeline(SimpleClock(interval),
                    TriggeredSource(url),
                    HTTPGetter(),
                    PureTransformer(function=lambda x: [target, x]),
                    WholeFileWriter()
    )


def weatherSaver():
    """Stores the weather web pages for local debugging purposes
    """
    from Kamaelia.File.Writing import SimpleFileWriter

    Pipeline(
        DataSource(["http://www.wetter24.de/wetter/berlin-alexanderplatz/10389.html"]),
        HTTPGetter(),
        SimpleFileWriter('/tmp/w24.html', mode="wb")
    ).run()
    Pipeline(
        DataSource(["http://sdo.gsfc.nasa.gov/data/"]),
        HTTPGetter(),
        SimpleFileWriter('/tmp/sdo.html', mode="wb")
    ).run()



def gribAnalyzer():
    """Analyzes grib data
    Currently in development, do not use.
    """
    analyzer = Pipeline(DataSource([(52.31, 13.23)]),
                        GribParser('/tmp/berlin.grb'),
                        ConsoleEchoer()
    ).activate()


def gribGetter():
    downloader = Pipeline(
        DataSource([
            "http://api.met.no/weatherapi/gribfiles/1.0/?area=north_europe;content=weather;content_type=application/octet-stream;"]),
        HTTPGetter(),
        SimpleFileWriter('/tmp/gribdata_north_europe.grb'),

    )


# def build_weatherScraper(interval=600, template="weather.html", location=None):
#     """Constructs a weathersite scraper, in ijon's c-beam style"""
#
#     rainradar = Pipeline(
#         TriggeredSource("http://wind.met.fu-berlin.de/loops/radar_100/R.NEW.gif"),
#         HTTPGetter(),
#         PureTransformer(function=lambda x: ["images/rainradar.gif", x]),
#     )
#
#     nasa_sdo = Pipeline(
#         siteScraper("http://sdo.gsfc.nasa.gov/data/",
#                     filterclass=NasaSDOFilter()
#         ),
#         HTTPGetter(),
#         PureTransformer(function=lambda x: ["images/nasa_sdo.jpg", x]),
#     )
#
#     w24 = Pipeline(
#         siteScraper("http://www.wetter24.de/wetter/berlin-alexanderplatz/10389.html",
#                     filterclass=Wetter24Filter(),
#                     decode=False
#         ),
#         PureTransformer(function=addtime),
#         DictTemplater(templater=MakoTemplater(template)),
#         PureTransformer(function=lambda x: [template + ".html", x]),
#     )
#
#     Getter = Graphline(RR=rainradar,
#                                NSDO=nasa_sdo,
#                                W24=w24,
#                                SPLIT=Fanout(['rainradar', 'nasa_sdo', 'w24']),
#                                linkages={
#                                    ("self", "inbox"): ("SPLIT", "inbox"),
#                                    ("SPLIT", "rainradar"): ("RR", "inbox"),
#                                    ("SPLIT", "nasa_sdo"): ("NSDO", "inbox"),
#                                    ("SPLIT", "w24"): ("W24", "inbox"),
#                                    ("RR", "outbox"): ("self", "outbox"),
#                                    ("NSDO", "outbox"): ("self", "outbox"),
#                                    ("W24", "outbox"): ("self", "outbox"),
#
#                                }
#     )
#
#     if location:
#         filewriter = Graphline(DS=DataSource([True]),
#                                IG=Getter,
#                                LOCN=PureTransformer(function=lambda x: [location + "/" + x[0], x[1]]),
#                                WFW=WholeFileWriter(),
#                                #CE=ConsoleEchoer(),
#                                linkages={
#                                    ("DS", "outbox"): ("IG", "inbox"),
#                                    ("IG", "outbox"): ("LOCN", "inbox"),
#                                    ("LOCN", "outbox"): ("WFW", "inbox")
#                                }
#         ).activate()
#     else:
#         webwriter = Graphline(SC=SimpleClock(interval),
#                               IG=Getter,
#                               WG=WebStore(),
#                               #CE=ConsoleEchoer(),
#                               linkages={
#                                   ("SC", "outbox"): ("IG", "inbox"),
#                                   ("IG", "outbox"): ("WG", "inbox")
#                               }
#         ).activate()


def build_nmeaPublisher(debug=True):
    """builds the nmea bus backplane and publishers

    Caution: Currently in debug mode (operates without serial but datasource)
    """
    log("Backplane: preparing")

    def debugSource():

        from Axon.ThreadedComponent import threadedcomponent
        import time

        class SlowOutputter(threadedcomponent):

            def __init__(self):
                super(SlowOutputter, self).__init__(queuelengths=1)

            def main(self):
                while 1:

                    if self.dataReady("inbox"):
                        self.send(self.recv("inbox"), "outbox")

                        t = time.time() + 1.2
                        while t > time.time():
                            self.pause(t - time.time())

                    else:
                        if self.dataReady("control"):
                            self.send(self.recv("control"), "signal")
                            return

        return Pipeline(SimpleClock(2),
                        TriggeredSource("NEXT"),
                        Chooser(["$GPALM,32,1,01,5,00,264A,4E,0A5E,FD3F,A11257,B8E036,536C67,2532C1,069,000*7B",
                                 "$GPALM,32,1,01,5,00,264A,4E,0A5E,FD3F,A11257,B8E036,536C67,2532C1,069,000*7B",
                                 "$GPRMC,162614,A,5230.5900,N,01322.3900,E,10.0,90.0,131006,1.2,E,A*13",
                                 "$SDDBT,60.46,f,18.43,M,10.07,F*0A",
                                 "$GPALM,32,1,01,5,00,264A,4E,0A5E,FD3F,A11257,B8E036,536C67,2532C1,069,000*7B",
                                 "$GPRMC,162614,A,5230.5900,N,01322.3900,E,12.0,75.0,131006,1.2,E,A*1A",
                                 "$SDDBT,75.02,f,22.87,M,12.50,F*0F",
                                 "$GPALM,32,1,01,5,00,264A,4E,0A5E,FD3F,A11257,B8E036,536C67,2532C1,069,000*7B",
                                 "$SDDBT,15,f,4.57,M,2.49,F*25",
                                 "$GPRMC,162614,A,5230.5900,N,01322.3900,E,12.3,72.0,131006,1.2,E,A*1E",
                                 "$GPRMC,162614,A,5230.5900,N,01322.3900,E,10.0,90.0,131006,1.2,E,A*13",
                                 ""], loop=True),
        ).activate()
    log("Backplane: Debug: ", debug)
    nmeaPublisher = Pipeline(
        debugSource() if debug else SerialReader('/dev/ttyUSB0'),
        NMEAParser(),
        PublishTo("NMEA")
    ).activate()


def build_nmeaSubscribers():
    log("Backplane: activating")

    Backplane("NMEA").activate()
    log("Backplane: active.")

    #    consoleLogger = Pipeline(SubscribeTo("NMEA"),
    #                             ConsoleEchoer()
    #    ).activate()


    testa = Pipeline(DataSource(['FOOBAR']),
                     Match(lambda x: x == 'FOOBAR'),
                     ConsoleEchoer()
    )  # .activate()

    # TODO: refactor for WebUI
    nmeaAnalyzer = Graphline(BP=SubscribeTo('NMEA'),
                             GPRMC=Match(lambda x: x['sen_type'] == "GPRMC"),
                             GPRMCDT=DictTemplater(templater=MakoTemplater('navdisplay.html')),
                             GPRMCPT=PureTransformer(lambda x: ("navdisplay.html", x)),
                             SDDBT=Match(lambda x: x['sen_type'] == "SDDBT"),
                             SDDBTPT=PureTransformer(lambda x: ("GEIL! TIEFENDATEN", x)),
                             UNCAUGHT=ConsoleEchoer(),
#                             WS=WebStore(),
                             linkages={
                                 ("BP", "outbox"): ("GPRMC", "inbox"),
                                 ("GPRMC", "outbox"): ("SDDBT", "inbox"),
                                 #("SDDBT", "outbox"): ("UNCAUGHT", "inbox"),
                                 ("GPRMC", "match"): ("GPRMCDT", "inbox"),
                                 ("GPRMCDT", "outbox"): ("GPRMCPT", "inbox"),
                                 ("GPRMCPT", "outbox"): ("WS", "inbox"),
                                 ("SDDBT", "match"): ("SDDBTPT", "inbox"),
                                 ("SDDBTPT", "outbox"): ("UNCAUGHT", "inbox")
                             }
    ).activate()

    # navDataGetter = Graphline(BP=SubscribeTo("NMEA"),
    #                           F=Filter(filter=nmeaFilter("GPRMC")),
    #
    #
    #                           CE=ConsoleEchoer(),
    #                           linkages={
    #                               ("BP", "outbox"): ("F", "inbox"),
    #                               ("F", "outbox"): ("DT", "inbox"),
    #                               ("DT", "outbox"): ("PT", "inbox"),
    #                               ("PT", "outbox"): ("CE", "inbox")
    #                           }
    # ).activate()
    #
    # trueCourseFinder = Pipeline(SubscribeTo("NMEA"),
    #                             Filter(filter=nmeaFilter("GPRMC")),
    #                             DictPicker('true_course'),
    #                             ConsoleEchoer()
    # ).activate()
    #
    # trueSpeedFinder = Pipeline(SubscribeTo("NMEA"),
    #                            Filter(filter=nmeaFilter("GPRMC")),
    #                            DictPicker('spd_over_grnd'),
    #                            ConsoleEchoer()
    # ).activate()
    #
    # nmeaAlmConsumer = Pipeline(SubscribeTo("NMEA"),
    #                            Filter(filter=nmeaFilter("GPALM")),
    #                            ConsoleEchoer()
    # ).activate()
    #
    # depthFinder = Pipeline(SubscribeTo("NMEA"),
    #                        Filter(filter=nmeaFilter("SDDBT")),
    #                        DictPicker('depth_meters'),
    #                        ConsoleEchoer()
    # ).activate()
    #
    # watertempFinder = Pipeline(SubscribeTo("NMEA"),
    #                            Filter(filter=nmeaFilter("SDMTW")),
    #                            DictPicker('temperature_water_celsius'),
    #                            ConsoleEchoer()
    # ).activate()


def build_ticktock():
    ticktock = Pipeline(SimpleClock(0.5),
                        ConsoleEchoer()
    ).activate()


#!/usr/bin/env python
# encoding: utf-8

__author__ = 'Alexader Bohn'
__version__ = (0, 1, 0)

"""
signalqueue/__init__.py

Provides the signalqueue registry and an autodiscover() function to populate it
from instances of AsyncSignal that it finds in either:

    a) modules named 'signals' in any of the members of INSTALLED_APPS, or
    b) modules that are specified in the settings.SQ_ADDITIONAL_SIGNALS list.
    
a la django.contrib.admin's autodiscover() and suchlike.

Created by FI$H 2000 on 2011-09-09.
Copyright (c) 2011 Objects In Space And Time, LLC. All rights reserved.

"""
import os, threading
from collections import defaultdict
from signalqueue.utils import import_module, logg

SQ_RUNMODES = {
    'SQ_SYNC':                      1, # synchronous operation -- fire signals concurrently with save() and cache pragma
    'SQ_ASYNC_MGMT':                2, # async operation -- we are running from the command line, fire signals concurrently
    'SQ_ASYNC_DAEMON':              3, # async operation -- deque images from cache, fire imagekit signals but don't save
    'SQ_ASYNC_REQUEST':             4, # async operation -- queue up signals on save() and cache pragma
}

SQ_ROOT = os.path.dirname(os.path.abspath(__file__))
SQ_DMV = defaultdict(set)

def autodiscover():
    """
    Auto-discover signals.py modules in the apps in INSTALLED_APPS;
    and fail silently when not present.
    
    N.B. this autdiscover() implementation is based on dajaxice_autodiscover in the
    Dajaxice module:
    
        https://github.com/jorgebastida/django-dajaxice/blob/master/dajaxice/core/Dajaxice.py#L155
    
    ... which in turn was inspired/copied from django.contrib.admin.autodiscover().
    
    """
    
    autodiscover.lock.acquire()
    
    try:
        import imp
        from django.conf import settings
        from signalqueue.dispatcher import AsyncSignal
        
        # Gather signals that any of the installed apps define in
        # their respective signals.py files:
        logg.info("")
        logg.info("*** Looking for AsyncSignal instances in %s apps..." % len(settings.INSTALLED_APPS))
        
        for appstring in settings.INSTALLED_APPS:
            
            try:
                app = import_module(appstring)
            except AttributeError:
                continue
            
            try:
                imp.find_module('signals', app.__path__)
            except ImportError:
                continue
            
            modstring = "%s.signals" % appstring
            mod = import_module(modstring)
            
            for name, thing in mod.__dict__.items():
                if isinstance(thing, AsyncSignal):
                    thing.name = name
                    thing.regkey = modstring
                    SQ_DMV[modstring].add(thing)
        
        if hasattr(settings, "SQ_ADDITIONAL_SIGNALS"):
            if isinstance(settings.SQ_ADDITIONAL_SIGNALS, (list, tuple)):
                
                logg.info("*** Registering additional signals: %s" % str(settings.SQ_ADDITIONAL_SIGNALS))
                
                for addendumstring in settings.SQ_ADDITIONAL_SIGNALS:
                    
                    try:
                        addendum = import_module(addendumstring)
                    except AttributeError, err:
                        # TODO: log this in a reliably sane manner
                        logg.warning("xxx Got AttributeError when loading an additional signal module: %s" % err)
                    
                    for name, thing in addendum.__dict__.items():
                        if isinstance(thing, AsyncSignal):
                            logg.info("*** Adding additional signal to %s: %s" % (addendumstring, thing))
                            thing.name = name
                            thing.regkey = addendumstring
                            SQ_DMV[addendumstring].add(thing)
    
    finally:
        autodiscover.lock.release()

autodiscover.lock = threading.Lock()

class Registrar(object):
    """
    Interface for the async signal registry.
    
    """
    queues = {}
    queue_name = None
    runmode = None
    
    
    

class SignalRegistryError(AttributeError):
    pass

class SignalDispatchError(AttributeError):
    pass




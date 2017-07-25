#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tools for interfacing IRIS data, ObsPy, and SAC input/output.
"""
from __future__ import print_function

import os

import obspy
from obspy.clients.fdsn import Client
from scipy import signal

from util_write_cap import *

def run_get_waveform(c, event, ref_time_place, ev_info):
    """
    Get SAC waveforms for an event

    basic usage:
        run_get_waveform(event)

    c              -  client
    event          -  obspy Event object
    ref_time_place -  reference time and place (other than origin time and place - for station subsetting)
    ev_info        -  event info (See run_getwaveform_input.py)
    ---------------- from old getwaveform.py ----------------------
    min_dist - minimum station distance (default = 20)
    max_dist - maximum station distance (default =300)
    before -   time window length before the event time (default= 100)
    after  -   time window length after the event time (default = 300)
    network -  network codes of potential stations (default=*)
    channel -  component(s) to get, accepts comma separated (default='BH*')
    ifresample_TF   - Boolean. Request resample or not. Default = False
    resample_freq   - sampling frequency to resample waveforms (default 20.0)
    ifrotate - Boolean, if true will output sac files rotated to baz
               unrotated sac files will also be written
    ifCapInp - Boolean, make weight files for CAP
    ifEvInfo - Boolean, output 'ev_info.dat' containg event info (True)
    ifRemoveResponse - Boolean, will remove response (True)
    ifDetrend - Boolean, will remove linear trend from data (True)
    ifDemean  - Boolean, will insult the data (True)
    scale_factor - scale all data by one value (10.0**2)
                    This usually puts the data in the units required by CAP
                    From m/s to cm/s
    pre_filt  - list, corner frequencies of filter to apply before deconv
                a good idea when deconvolving (ifRemoveResponse=True)
    """
    
    evtime = event.origins[0].time
    reftime = ref_time_place.origins[0].time

    if ev_info.idb==1:
        print("Preparing request for IRIS ...")
        # BK network doesn't return data when using the IRIS client.
        # this option switches to NCEDC if BK is 
        if "BK" in ev_info.network:
            client_name = "NCEDC"
            print("\nWARNING. Request for BK network. Switching to NCEDC client")
            c = Client("NCEDC")
        else:
            client_name = "IRIS" 

        print("Download stations...")
        stations = c.get_stations(network=ev_info.network, station=ev_info.station, 
                                  channel=ev_info.channel,
                                  starttime=reftime - ev_info.tbefore_sec, endtime=reftime + ev_info.tafter_sec,
                                  level="response")
        inventory = stations    # so that llnl and iris scripts can be combined
        print("Printing stations")
        print(stations)
        print("Done Printing stations...")
        sta_limit_distance(ref_time_place, stations, min_dist=ev_info.min_dist, max_dist=ev_info.max_dist, min_az=ev_info.min_az, max_az=ev_info.max_az)
        
        print("Downloading waveforms...")
        bulk_list = make_bulk_list_from_stalist(
            stations, reftime - ev_info.tbefore_sec, reftime + ev_info.tafter_sec, channel=ev_info.channel)
        stream_raw = c.get_waveforms_bulk(bulk_list)
            
    elif ev_info.idb==3:
        client_name = "LLNL"
        print("Preparing request for LLNL ...")

        # Get event an inventory from the LLNL DB.
        event_number = int(event.event_descriptions[0].text)
        # event = llnl_db_client.get_obspy_event(event)
        inventory = c.get_inventory()
        
        print("--> Total stations in LLNL DB: %i" % (
                len(inventory.get_contents()["stations"])))
        sta_limit_distance(event, inventory, min_dist=ev_info.min_dist, max_dist=ev_info.max_dist, min_az=ev_info.min_az, max_az=ev_info.max_az)
        print("--> Stations after filtering for distance: %i" % (
                len(inventory.get_contents()["stations"])))

        stations = set([sta.code for net in inventory for sta in net])
        
        _st = c.get_waveforms_for_event(event_number)
        stream_raw = obspy.Stream()
        for tr in _st:
            if tr.stats.station in stations:
                stream_raw.append(tr)
    
    # set reftime
    stream = obspy.Stream()
    stream = set_reftime(stream_raw, evtime)

    print("--> Adding SAC metadata...")
    st2 = add_sac_metadata(stream,idb=ev_info.idb, ev=event, stalist=inventory)

    # Do some waveform QA
    # - (disabled) Throw out traces with missing data
    # - log waveform lengths and discrepancies
    # - Fill-in missing data -- Carl request
    do_waveform_QA(st2, client_name, event, evtime, ev_info.tbefore_sec, ev_info.tafter_sec)

    if ev_info.demean:
        st2.detrend('demean')

    if ev_info.detrend:
        st2.detrend('linear')

    if ev_info.ifFilter:
        prefilter(st2, ev_info.f1, ev_info.f2, ev_info.zerophase, ev_info.corners, ev_info.filter_type)

    if ev_info.removeResponse:
        resp_plot_remove(st2, ev_info.ipre_filt, ev_info.pre_filt, ev_info.iplot_response, ev_info.scale_factor, stations, ev_info.outformat)
    else:
        # output RAW waveforms
        decon=False
        print("WARNING -- NOT correcting for instrument response")

    if scale_factor > 0:
        amp_rescale(st2, ev_info.scale_factor)
        if ev_info.idb ==3:
            amp_rescale_llnl(st2, ev_info.scale_factor)


    # Set the sac header KEVNM with event name
    # This applies to the events from the LLNL database
    # NOTE this command is needed at the time of writing files, so it has to
    # be set early
    st2, evname_key = rename_if_LLNL_event(st2, evtime)

    # Get list of unique stations + locaiton (example: 'KDAK.00')
    stalist = []
    for tr in st2.traces:
        #stalist.append(tr.stats.station)
        stalist.append(tr.stats.network + '.' + tr.stats.station +'.'+ tr.stats.location + '.'+ tr.stats.channel[:-1])

    # Crazy way of getting a unique list of stations
    stalist = list(set(stalist))

    # match start and end points for all traces
    st2 = trim_maxstart_minend(stalist, st2, client_name, event, evtime, ev_info.resample_TF, ev_info.resample_freq, ev_info.tbefore_sec, ev_info.tafter_sec)
    if len(st2) == 0:
        raise ValueError("no waveforms left to process!")

    if ev_info.resample_TF == True:
    # NOTE !!! tell the user if BOTH commands are disabled NOTE !!!
        if (client_name == "IRIS"):
            resample(st2, freq=ev_info.resample_freq)
        elif (client_name == "LLNL"):
            resample_cut(st2, ev_info.resample_freq, evtime, ev_info.tbefore_sec, ev_info.tafter_sec)
    else:
        print("WARNING. Will not resample. Using original rate from the data")

    # save raw waveforms in SAC format
    path_to_waveforms = evname_key + "/RAW"
    write_stream_sac_raw(stream_raw, path_to_waveforms, evname_key, ev_info.idb, event, stations=inventory)

    # Taper waveforms (optional; Generally used when data is noisy- example: HutchisonGhosh2016)
    # https://docs.obspy.org/master/packages/autogen/obspy.core.trace.Trace.taper.html
    # To get the same results as the default taper in SAC, use max_percentage=0.05 and leave type as hann.
    if ev_info.Taper:
        st2.taper(max_percentage=ev_info.Taper, type='hann',max_length=None, side='both')

    # save processed waveforms in SAC format
    path_to_waveforms = evname_key 
    write_stream_sac(st2, path_to_waveforms, evname_key)

    if ev_info.ifrotateRTZ:
        rotate_and_write_stream(st2, evname_key, ev_info.icreateNull, ev_info.ifrotateUVW)

    if ev_info.ifCapInp:
        write_cap_weights(st2, evname_key, client_name, event)

    if ev_info.ifEvInfo:
        write_ev_info(event, evname_key)

    if ev_info.ifplot_spectrogram:
        plot_spectrogram(st2, evname_key)

    if ev_info.ifsave_sacpaz:
        write_resp(inventory,evname_key)

    # save station inventory as XML file
    xmlfilename = evname_key + "/stations.xml"
    stations.write(xmlfilename, format="stationxml", validate=True)

import obspy
import read_event_obspy_file as reof
from getwaveform import *

def get_ev_info(ev_info,iex):
# ===============================================================
# Vipul Silwal: 6 moment tensors in Tape et al. (2018 Nature Geoscience); 
# python run_getwaveform.py event_input_nennuc 0
    if iex == 0:
        ev_info.use_catalog = 0
        # -------------------------------------------------
        # VLFE + EQ (from 2012 Trigger paper)
        # Note: No PS stations when extracting through IRIS
        #ev_info.otime = obspy.UTCDateTime("2012-04-11T09:21:57.444")
        #ev_info.elat = 64.9222
        #ev_info.elon = -148.9461
        #ev_info.edep = 16000
        #ev_info.emag = 3.80
        # -------------------------------------------------
        # VLFE
        #ev_info.otime = obspy.UTCDateTime("2013-03-12T07:39:50.214")
        #ev_info.elat = 64.7161
        #ev_info.elon = -148.9505
        #ev_info.edep = 23000
        #ev_info.emag = 3.5
        # -------------------------------------------------
        # VLFE
        #ev_info.otime = obspy.UTCDateTime("2015-09-12T03:25:12.711")
        #ev_info.elat = 65.1207
        #ev_info.elon = -148.6646
        #ev_info.edep = 21000
        #ev_info.emag = 3.80
        # -------------------------------------------------
        # EQ
        #ev_info.otime = obspy.UTCDateTime("2015-10-22T13:16:15.794")
        #ev_info.elat = 64.7334
        #ev_info.elon = -149.0388
        #ev_info.edep = 18000
        #ev_info.emag = 2.6
        # -------------------------------------------------
        # EQ
        #ev_info.otime = obspy.UTCDateTime("2015-10-31T02:56:35.572")
        #ev_info.elat = 64.4285
        #ev_info.elon = -149.6969
        #ev_info.edep = 25000
        #ev_info.emag = 3.40
        # -------------------------------------------------
        # VLFE + EQ
        ev_info.otime = obspy.UTCDateTime("2016-01-14T19:04:10.727")
        ev_info.elat = 64.6827
        ev_info.elon = -149.2479
        ev_info.edep = 17000
        ev_info.emag = 3.70
        # Output pole-zero file (Chen Ji needed this for source estimation)
        #ev_info.ifsave_sacpaz = True
        # -------------------------------------------------
        
        ev_info.min_dist = 0
        ev_info.max_dist = 200
        ev_info.tbefore_sec = 100
        ev_info.tafter_sec = 600
        ev_info.network = 'AV,CN,AT,TA,AK,XV,II,IU,US'
        # ev_info.network = 'XV,AK'
        ev_info.channel = 'BH?,HH?'
        # for CAP
        ev_info.scale_factor = 100
        ev_info.resample_freq = 50

    return(ev_info)

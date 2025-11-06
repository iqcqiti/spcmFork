"""  
Spectrum Instrumentation GmbH (c) 2024

16_dds_test_trigger_envlope.py

Continuous changes - use one carrier to jump between different frequencies that are send through the FIFO

Example for analog replay cards (AWG) for the the M4i and M4x card-families with installed DDS option.

See the README file in the parent folder of this examples directory for information about how to use this example.

See the LICENSE file for the conditions under which this software may be used and distributed.
"""

import spcm
from spcm import units


import numpy as np
import matplotlib.pyplot as plt

# Set the highest process priority to the Python process, to enable highest possible command streaming

card : spcm.Card
# with spcm.Card('/dev/spcm0') as card:                         # if you want to open a specific card
# with spcm.Card('TCPIP::192.168.1.10::inst0::INSTR') as card:  # if you want to open a remote card
with spcm.Card(serial_number=22189) as card:                  # if you want to open a card by its serial number
# with spcm.Card(card_type=spcm.SPCM_TYPE_AO) as card:            # if you want to open the first card of a specific type
    print("Using card:", card)

    # setup card for DDS
    card.card_mode(spcm.SPC_REP_STD_DDS)

    # Setup the channels
    channels = spcm.Channels(card)
    channels.enable(True)
    channels.output_load(50 * units.ohm)
    channels.amp(1 * units.V)
    card.write_setup() # IMPORTANT! this turns on the card's system clock signals, that are required for DDS to work
    
    # Setup DDS
    dds = spcm.DDS(card)
    dds.reset()

    dds.data_transfer_mode(spcm.SPCM_DDS_DTM_DMA)
    fixed_freq_Hz = 200 * units.MHz
    
    # Amplitude ramp settings
    amp_start = 0 * units.percent
    dds.trg_src(spcm.SPCM_DDS_TRG_SRC_TIMER)

    dds.trg_timer(0.0000001 * units.s)
    dds[0].amplitude_slope(0)
    dds[0].freq(fixed_freq_Hz)
    dds[0].amp(amp_start)
    dds.exec_at_trg()
    
    
    dds.trg_timer(0.0000005 * units.s)
    dds[0].amplitude_slope(1000000)
    dds.exec_at_trg()

    dds.trg_timer(0.0000005 * units.s)
    dds[0].amplitude_slope(0)
    dds.exec_at_trg()
    
    dds.trg_src(spcm.SPCM_DDS_TRG_SRC_NONE)
    dds[0].amplitude_slope(0)
    dds[0].amp(0)
    dds.exec_at_trg()
    
    dds.write_to_card()

    # Start command including enable of trigger engine
    card.start(spcm.M2CMD_CARD_ENABLETRIGGER, spcm.M2CMD_CARD_FORCETRIGGER)

    input("Press Enter to Exit")



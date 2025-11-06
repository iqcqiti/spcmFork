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
    channels.amp(1 * units.V)
    card.write_setup() # IMPORTANT! this turns on the card's system clock signals, that are required for DDS to work
    
    # Setup DDS
    dds = spcm.DDS(card)
    dds.reset()

    dds.data_transfer_mode(spcm.SPCM_DDS_DTM_DMA)

    # Start the DDS test
    num_cores = 1 # len(dds)
    # Fixed frequency for all cores
    fixed_freq_Hz = 200 * units.MHz
    
    # Amplitude ramp settings
    num_segments = 16
    total_time_s = .000005 * units.s
    amp_start = 0 * units.percent
    amp_end = 100 * units.percent

    # STEP 0 - Initialize fixed frequency and starting amplitude
    dds.freq_ramp_stepsize(1000)
    dds.trg_timer(0.0000001 * units.s)
    dds.trg_src(spcm.SPCM_DDS_TRG_SRC_TIMER)
    for core in dds[0:num_cores]:
        core.amp(amp_start)
        core.freq(fixed_freq_Hz)
    dds.exec_at_trg()
    dds.write_to_card()

    # STEP 1 - Start the amplitude ramp
    period_s = total_time_s / num_segments # seconds
    dds.trg_timer(period_s) # after 5.0 s stop the ramp
    # Prepare amplitude steps
    amp_values = np.linspace(amp_start.magnitude, amp_end.magnitude, num_segments+1)
    t = np.linspace(0, total_time_s.magnitude, num_segments+1)
    # plt.figure(figsize=(7,7))
    # plt.plot(t, amp_values, 'o-', label='Amplitude (%)')
    # plt.xlabel('Time (s)')
    # plt.ylabel('Amplitude (%)')
    # plt.title('Amplitude Ramp (Fixed Frequency)')
    # plt.show(block=False)
        # ...removed obsolete frequency ramp plotting...
        
    # plt.legend()
    # plt.xlabel('t(s)')
    # plt.ylabel('y(Hz)')

    plt.show(block=False)

    # Do the amplitude steps
    for j in range(num_segments+1):
        for core in dds[0:num_cores]:
            core.amp(amp_values[j] * units.percent)
        dds.exec_at_trg()

    # STEP 2 - Stop the ramp (hold at final amplitude)
    for core in dds[0:num_cores]:
        core.amp(0)
    dds.exec_at_trg()
    dds.write_to_card()

    # Start command including enable of trigger engine
    card.start(spcm.M2CMD_CARD_ENABLETRIGGER, spcm.M2CMD_CARD_FORCETRIGGER)

    input("Press Enter to Exit")



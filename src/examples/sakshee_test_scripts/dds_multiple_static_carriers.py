"""  
Spectrum Instrumentation GmbH (c) 2024

2_dds_multiple_static_carriers.py

Multiple static carriers - this example shows the DDS functionality with 20 carriers with individual but fixed frequencies on one channel. 

Example for analog replay cards (AWG) for the the M4i and M4x card-families with installed DDS option.

See the README file in the parent folder of this examples directory for information about how to use this example.

See the LICENSE file for the conditions under which this software may be used and distributed.
"""

import spcm
from spcm import units
import numpy as np
from time import sleep


card : spcm.Card
# with spcm.Card('/dev/spcm0') as card:                         # if you want to open a specific card
# with spcm.Card('TCPIP::192.168.1.10::inst0::INSTR') as card:  # if you want to open a remote card
# with spcm.Card(serial_number=12345) as card:                  # if you want to open a card by its serial number
with spcm.Card(card_type=spcm.SPCM_TYPE_AO) as card:             # if you want to open the first card of a specific type

    # setup card for DDS
    card.card_mode(spcm.SPC_REP_STD_DDS)

    # Setup the card
    channels = spcm.Channels(card) # enable all channels
    channels.enable(True)
    channels.output_load(50 * units.ohm)
    channels.amp(2 * units.V)
    card.write_setup() # IMPORTANT! this turns on the card's system clock signals, that are required for DDS to work
    
    # Setup DDS
    dds = spcm.DDS(card, channels=channels)
    dds.reset()

    # # Start the test
    num_cores = len(dds)-1
    num_cores = 1

    print("The Number of cores used: ", num_cores)
    # Note that the last core is not working properly for this channel. As, it is assigned to the second channel 
    # for core in dds[:-1]:
    start_freq = 105
    stop_freq = 135
    total_ampl_usage = 100 * units.percent 

    freq_list = np.linspace(start_freq, stop_freq, num_cores+1)
    freq_sep = freq_list[1] - freq_list[0]
    print(f"Frequency separation is {freq_sep * units.MHz}")
    print(freq_list[0:num_cores])

    for core in dds[0:num_cores]:
        print(core)

        # if int(core) == 0:
        #     core.amp(2.5*units.percent)
        #     print("  Amp: ",2*units.percent)
        
        # if int(core) == 1:
        #     core.amp(1.5*units.percent)

        # if int(core) == 2:
        #     core.amp(2*units.percent)

        # set the amplitude for each tone
        amp_per_freq = total_ampl_usage / num_cores 
        core.amp(amp_per_freq)
        print("  Amp: ",amp_per_freq)

        # set the frequency for each tone
        freq_i = freq_list[int(core)] * units.MHz
        core.freq(freq_i)
        print("  Freq: ",freq_i)
    
    ###################################
    # single tone frequency
    # core = dds[1]

    # amp = 100 * units.percent
    # freq = 120 * units.MHz
    # print("  Amp: ",amp)
    # print("  Freq: ",freq)
    # core.amp(amp)
    # core.freq(freq)

    ###################################

    # dds[0].amp(100 * units.percent)
    # dds[0].freq(100 * units.MHz)
    # 40 --> -55

    dds.exec_at_trg()
    dds.write_to_card()

    # Start command including enable of trigger engine
    card.start(spcm.M2CMD_CARD_ENABLETRIGGER, spcm.M2CMD_CARD_FORCETRIGGER)

    input("Press Enter to Exit")

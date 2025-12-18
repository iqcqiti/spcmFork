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
import time

def generate_gaussian_slopes(total_duration, num_segments, amplitude=1.0, mean=0.0, std_dev=1.0):
    """
    Generates the slopes for a truncated Gaussian pulse profile.

    This function calculates a truncated Gaussian pulse over a specified duration and
    then determines the slope between discrete time points, which can be sent to an AWG.

    Args:
        total_duration (float): The total time duration of the pulse.
        num_segments (int): The number of segments (or slope changes) to use.
        amplitude (float, optional): The amplitude of the Gaussian pulse ($A$).
        mean (float, optional): The mean of the Gaussian pulse ($\mu$).
        std_dev (float, optional): The standard deviation of the Gaussian pulse ($\sigma$).

    Returns:
        tuple: A tuple containing:
            - slopes (numpy.ndarray): The slopes between each time point.
            - time_points (numpy.ndarray): The time points at which the slopes are valid.
    """
    # Define the time step
    time_step = total_duration / num_segments
    
    # Generate the time points for the pulse
    time_points = np.linspace(-total_duration / 2, total_duration / 2, num_segments + 1)
    
    # Calculate the values of the Gaussian function at each time point
    # The Gaussian function is given by: $y = A \cdot e^{-\frac{(t-\mu)^2}{2\sigma^2}}$
    gaussian_values = amplitude * np.exp(-((time_points - mean)**2) / (2 * std_dev**2))
    
    # Calculate the slopes between consecutive points
    # slope = (change in y) / (change in x)
    slopes = np.diff(gaussian_values) / time_step
    
    return slopes, time_points

def plot_gaussian_pulse(time_points, slopes, total_duration, num_segments, amplitude=1.0, mean=0.0, std_dev=1.0):
    """
    Plots the reconstructed Gaussian pulse and the original curve for comparison.

    Args:
        time_points (numpy.ndarray): The time points of the segmented pulse.
        slopes (numpy.ndarray): The slopes for each segment.
        total_duration (float): The total time duration of the pulse.
        num_segments (int): The number of segments used.
        amplitude (float, optional): The amplitude of the Gaussian pulse ($A$).
        mean (float, optional): The mean of the Gaussian pulse ($\mu$).
        std_dev (float, optional): The standard deviation of the Gaussian pulse ($\sigma$).
    """
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Create the figure and axes
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot the original Gaussian function (for reference)
    t_full = np.linspace(-total_duration / 2, total_duration / 2, 500)
    gaussian_full = amplitude * np.exp(-((t_full - mean)**2) / (2 * std_dev**2))
    ax.plot(t_full, gaussian_full, label='Original Gaussian Pulse', color='gray', linestyle='--')
    
    # Plot the reconstructed pulse from the calculated segments
    ax.plot(time_points, amplitude * np.exp(-((time_points - mean)**2) / (2 * std_dev**2)), 
            'o-', color='blue', label='Reconstructed Pulse from Segments')
            
    # Add vertical lines to indicate the segments
    for i in range(1, len(time_points)):
        ax.axvline(x=time_points[i], color='red', linestyle=':', alpha=0.5)
        # Add a segment number and slope label
        if i <= len(time_points) - 1:
            x_pos = (time_points[i] + time_points[i-1]) / 2
            ax.text(x_pos, 0.05, f'Seg. {i}\nSlope: {slopes[i-1]:.2f}', ha='center', va='bottom', transform=ax.get_xaxis_transform(), fontsize=8, color='black')

    # Add labels and title
    ax.set_title('Truncated Gaussian Pulse from AWG Slopes')
    ax.set_xlabel('Time')
    ax.set_ylabel('Amplitude')
    ax.legend()
    ax.grid(True)
    
    # Display the plot
    plt.show(block=False)

# Set the highest process priority to the Python process, to enable highest possible command streaming
class Card_Controller:
    def __init__(self, Card: spcm.Card):
        self.card = Card
        self.init_card()
    def stop_card(self):
        self.card.stop() # have to reset the dds for reprogramming
    def start_card(self):
        self.card.start(spcm.M2CMD_CARD_ENABLETRIGGER)
    def reset_dds(self,DMA=True):
        self.dds.reset()
        if DMA:
            self.dds.data_transfer_mode(spcm.SPCM_DDS_DTM_DMA)
        else:   
            self.dds.data_transfer_mode(spcm.SPCM_DDS_DTM_SINGLE)

    def program_card(self, pulse_slopes, time_step, fixed_freq_Hz, loop_count):

        for i in range(loop_count): # loop to allow multiple triggers
            self.dds.trg_src(spcm.SPCM_DDS_TRG_SRC_CARD)
            self.dds[0].amplitude_slope(0)
            self.dds[0].freq(fixed_freq_Hz)
            self.dds[0].amp(0)
            self.dds.exec_at_trg()
            self.dds.trg_src(spcm.SPCM_DDS_TRG_SRC_TIMER) 	
            ##################################################################################
            # Slopes
            self.dds.trg_timer(time_step * units.s)

            # Loop through the slopes and send them to the AWG
            for i in range(len(pulse_slopes)):
                self.dds[0].amplitude_slope(pulse_slopes[i] * 1e6) # The slope is multiplied by 1e6 for dac units
                self.dds.exec_at_trg()

            ######## Gaussian envelope end ########
            
            # self.dds.trg_src(spcm.SPCM_DDS_TRG_SRC_NONE)
            self.dds[0].amplitude_slope(0)
            self.dds[0].amp(0)
            self.dds.exec_at_trg()
        self.dds.trg_src(spcm.SPCM_DDS_TRG_SRC_CARD)
        self.dds.exec_now()

    def program_sine_wave(self, freq, amplitude, duration, loop_count,start_seq=False):
        if not isinstance(freq, list):
            freq = [freq]
        if not isinstance(amplitude, list):
            amplitude = [amplitude]


        for _ in range(loop_count):
            self.dds.trg_src(spcm.SPCM_DDS_TRG_SRC_CARD)
            if not start_seq:
                self.dds.exec_now()
            else:
                if _ > 0 :
                    self.dds.exec_now()
            self.dds[0].freq(0)
            self.dds[0].amp(0)
            self.dds.exec_at_trg()
            self.dds[0].freq(freq[0])
            self.dds[0].amp(amplitude[0])


            self.dds.trg_src(spcm.SPCM_DDS_TRG_SRC_TIMER)
            self.dds.trg_timer(duration * units.s)
            self.dds.exec_now()

            self.dds[0].freq(0)
            self.dds[0].amp(0)
            self.dds.exec_at_trg()

    def write_to_card(self):            
        self.dds.write_to_card()

            

    def program_gaussian_envelope(self,total_duration,freq, num_segments, amplitude=1.0, mean=0.0, std_dev=1.0,loop_count=100):

        # Pulse and AWG parameters
        # The duration was increased to ensure the time_step is a valid, non-zero value for the AWG.
        time_step = total_duration / num_segments
        print("Time step:", time_step)
        # Get hardware-defined min/max slope values
        min_slope = self.card.get_d(spcm.SPC_DDS_AVAIL_AMP_SLOPE_MIN)
        max_slope = self.card.get_d(spcm.SPC_DDS_AVAIL_AMP_SLOPE_MAX)
        amp_step_size = self.card.get_d(spcm.SPC_DDS_AMP_RAMP_STEPSIZE)
        print(f"Hardware-defined amplitude ramp step size: {amp_step_size}")

        print(f"Hardware-defined amplitude slope range: Min={min_slope*1e-6:.2f} V/us, Max={max_slope*1e-6:.2f}V/us")
        # Generate the slopes and time points
        pulse_slopes, time_points = generate_gaussian_slopes(
            total_duration=total_duration,
            num_segments=num_segments,
            amplitude=amplitude,
            mean=mean,
            std_dev=std_dev
        )
        print("Slopes:", pulse_slopes)

        # Plot the pulse for visualization
        #plot_gaussian_pulse(time_points, pulse_slopes, total_duration, num_segments, amplitude, mean, std_dev)

        self.program_card(pulse_slopes, time_step, freq, loop_count)
    
    def init_card(self):
        
        self.card.card_mode(spcm.SPC_REP_STD_DDS)
        # Setup the channels
        self.channels = spcm.Channels(self.card)
        self.channels.enable(True)
        self.channels.output_load(50 * units.ohm)
        self.channels.amp(2 * units.V)

        self.trigger = spcm.Trigger(self.card)
        self.trigger.or_mask(spcm.SPC_TMASK_EXT0) # disable default software trigger
        self.trigger.ext0_mode(spcm.SPC_TM_POS) # positive edge
        self.trigger.ext0_level0(1 * units.V) # Trigger level is 1.5 V (1500 mV)
        self.trigger.ext0_coupling(spcm.COUPLING_DC) # set DC coupling
        self.trigger.delay(0) # no trigger delay

        self.card.write_setup() # IMPORTANT! this turns on the card's system clock signals, that are required for DDS to work

        # Setup DDS
        self.dds = spcm.DDS(self.card)
        self.dds.data_transfer_mode(spcm.SPCM_DDS_DTM_SINGLE)


    def reset_card(self):
        self.card.reset()
        self.init_card()

awg_card : spcm.Card
with spcm.Card(serial_number=22189) as awg_card:# if you want to open a card by its serial number

    cc= Card_Controller(awg_card)
    cc.reset_card()

    fixed_freq_Hz = 1 * units.MHz
    ######## Guassian envelope ########
    # Parameters for the Gaussian pulse
    amplitude = 1       # Amplitude ($A$)
    mean = 0.0      # Mean ($\mu$)
    std_dev = 0.005   # Standard deviation ($\sigma$)

    # Pulse and AWG parameters
    # The duration was increased to ensure the time_step is a valid, non-zero value for the AWG.
    duration = 10*1e-6    # Total time duration of the pulse (e.g., 10 microseconds)
    segments = 20         # Number of segments for the AWG


    cc.program_sine_wave(fixed_freq_Hz, 1, 5e-6
                           , loop_count=2, start_seq=True)
    cc.program_sine_wave(fixed_freq_Hz, 1, 5e-6
                           , loop_count=2)
    cc.program_gaussian_envelope(
        total_duration=duration,
        freq=fixed_freq_Hz,
        num_segments=segments,
        amplitude=amplitude,
        mean=mean,
        std_dev=std_dev,
        loop_count=2
    )   
    cc.program_sine_wave(fixed_freq_Hz, 1, 5e-6
                           , loop_count=2)
    cc.program_gaussian_envelope(
        total_duration=duration,
        freq=fixed_freq_Hz,
        num_segments=segments,
        amplitude=amplitude,
        mean=mean,
        std_dev=std_dev,
        loop_count=2
    )   
    cc.program_sine_wave(fixed_freq_Hz, 1, 5e-6
                           , loop_count=2)

    cc.write_to_card()
    cc.start_card()
    
    print("Waiting for trigger... (Signal should run for 1ms and stop)")
    # monitor the triggers sent from external generator
    tc_old = -1
    while True:
        time.sleep(0.01)
        tc = cc.trigger.trigger_counter()

        if tc != tc_old:
            tc_old = tc
            print(f"Trigger count: {tc}", flush=True)
    input("DDS Gaussian envelope programmed. Press Enter to stop and exit...")    

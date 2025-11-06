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
        mean (float, optional): The mean of the Gaussian pulse (r'$\mu$').
        std_dev (float, optional): The standard deviation of the Gaussian pulse (r'$\sigma$').

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
        mean (float, optional): The mean of the Gaussian pulse (r'$\mu$').
        std_dev (float, optional): The standard deviation of the Gaussian pulse (r'$\sigma$').
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

def run_trigger_and_pulse_sequence(card, dds, trigger, pulse_slopes, time_step):
    """
    Sets up the card, waits for a trigger, and sends the Gaussian pulse.
    """
    # Start command including enable of trigger engine
    card.start(spcm.M2CMD_CARD_ENABLETRIGGER, spcm.M2CMD_CARD_FORCETRIGGER)
    #print("Detecting external trigger...")
    
    # Wait for a new trigger to occur
    start_trigger_count = trigger.trigger_counter()
    while trigger.trigger_counter() == start_trigger_count:
        time.sleep(1e-10)  # Sleep for 0.1 ns to avoid busy waiting

    #print(f"Trigger {trigger.trigger_counter()} detected at {time.strftime('%H:%M:%S')}")

    # Stop the card
    card.stop()
    
    # Set the amplitude ramp settings
    dds.trg_src(spcm.SPCM_DDS_TRG_SRC_CARD)
    dds[0].amplitude_slope(0)
    dds[0].freq(200 * units.MHz)
    dds[0].amp(0 * units.percent)
    dds.exec_at_trg()
    dds.trg_src(spcm.SPCM_DDS_TRG_SRC_TIMER) 	
    
    # Set the trigger timer for each segment
    dds.trg_timer(time_step * units.s)

    # Loop through the slopes and send them to the AWG
    for slope_value in pulse_slopes:
        # Clamp the slope value to the hardware-defined range
        min_slope = card.get_d(spcm.SPC_DDS_AVAIL_AMP_SLOPE_MIN)
        max_slope = card.get_d(spcm.SPC_DDS_AVAIL_AMP_SLOPE_MAX)
        if slope_value > max_slope:
            slope_value = max_slope
        elif slope_value < min_slope:
            slope_value = min_slope
        
        dds[0].amplitude_slope(slope_value * 1e6) # The slope is multiplied by 1e6 for dac units
        dds.exec_at_trg()
    
    dds.trg_src(spcm.SPCM_DDS_TRG_SRC_NONE)
    dds[0].amplitude_slope(0)
    dds[0].amp(0)
    dds.exec_at_trg()
    dds.write_to_card()


# --- Main script ---

# Set the highest process priority to the Python process, to enable highest possible command streaming
card : spcm.Card
# with spcm.Card('/dev/spcm0') as card:                         # if you want to open a specific card
# with spcm.Card('TCPIP::192.168.1.10::inst0::INSTR') as card:  # if you want to open a remote card
with spcm.Card(serial_number=22189) as card: # if you want to open a card by its serial number
# with spcm.Card(card_type=spcm.SPCM_TYPE_AO) as card:            # if you want to open the first card of a specific type
    print("Using card:", card)

    # setup card for DDS
    card.card_mode(spcm.SPC_REP_STD_DDS)

    # Setup the channels
    channels = spcm.Channels(card)
    channels.enable(True)
    channels.output_load(50 * units.ohm)
    channels.amp(2 * units.V)
    
    trigger = spcm.Trigger(card)
    trigger.or_mask(spcm.SPC_TMASK_EXT0) # disable default software trigger
    trigger.ext0_mode(spcm.SPC_TM_POS) # positive edge
    trigger.ext0_level0(0.5 * units.V) # Trigger level is 1.5 V (1500 mV)
    trigger.ext0_coupling(spcm.COUPLING_DC) # set DC coupling
    trigger.delay(0) # no trigger delay
    
    card.write_setup() # IMPORTANT! this turns on the card's system clock signals, that are required for DDS to work
    
    # Setup DDS
    dds = spcm.DDS(card)
    dds.reset()
    dds.data_transfer_mode(spcm.SPCM_DDS_DTM_DMA)
    
    ######## Guassian envelope (calculated only once) ########
    # Parameters for the Gaussian pulse
    amplitude = 20000       # Amplitude ($A$)
    mean = 0.0      # Mean (r'$\mu$')
    std_dev = 0.5   # Standard deviation (r'$\sigma$')
    
    # Pulse and AWG parameters
    duration = 10.0e-6    # Total time duration of the pulse (e.g., 10 microseconds)
    segments = 4         # Number of segments for the AWG
    time_step = duration / segments
    print("Time step:", time_step)
    
    # Get hardware-defined min/max slope values and step size
    min_slope = card.get_d(spcm.SPC_DDS_AVAIL_AMP_SLOPE_MIN)
    max_slope = card.get_d(spcm.SPC_DDS_AVAIL_AMP_SLOPE_MAX)
    amp_step_size = card.get_d(spcm.SPC_DDS_AMP_RAMP_STEPSIZE)
    print(f"Hardware-defined amplitude ramp step size: {amp_step_size}")
    print(f"Hardware-defined amplitude slope range: Min={min_slope*1e-6:.2f} V/us, Max={max_slope*1e-6:.2f}V/us")

    # Generate the slopes and time points
    pulse_slopes, time_points = generate_gaussian_slopes(
        total_duration=duration,
        num_segments=segments,
        amplitude=amplitude,
        mean=mean,
        std_dev=std_dev
    )
    print("Calculated Slopes:", pulse_slopes)

    # Plot the pulse for visualization
    plot_gaussian_pulse(time_points, pulse_slopes, duration, segments, amplitude, mean, std_dev)
    
    # Loop to continuously run the pulse sequence on trigger
    while True:
        run_trigger_and_pulse_sequence(card, dds, trigger, pulse_slopes, time_step)
        
    print("Exiting...")
    card.stop()
    input("Press Enter to Exit")

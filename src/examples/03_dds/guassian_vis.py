import numpy as np
import matplotlib.pyplot as plt

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

def plot_gaussian_pulse(time_points, total_duration, num_segments, amplitude=1.0, mean=0.0, std_dev=1.0):
    """
    Plots the reconstructed Gaussian pulse and the original curve for comparison.

    Args:
        time_points (numpy.ndarray): The time points of the segmented pulse.
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
        # Add a segment number label
        if i <= len(time_points) - 1:
            x_pos = (time_points[i] + time_points[i-1]) / 2
            ax.text(x_pos, 0.05, f'Seg. {i}', ha='center', va='bottom', transform=ax.get_xaxis_transform(), fontsize=8, color='black')

    # Add labels and title
    ax.set_title('Truncated Gaussian Pulse from AWG Slopes')
    ax.set_xlabel('Time')
    ax.set_ylabel('Amplitude')
    ax.legend()
    ax.grid(True)
    
    # Display the plot
    plt.show()

if __name__ == "__main__":
    # --- Gaussian Coefficients ---
    A = 1.0       # Amplitude ($A$)
    mu = 0.0      # Mean ($\mu$)
    sigma = 0.5   # Standard deviation ($\sigma$)
    
    # --- Pulse Parameters ---
    duration = 3.0    # Total time duration of the pulse
    segments = 15     # Number of segments for the AWG
    
    # --- Generate the slopes and time points ---
    pulse_slopes, time_points = generate_gaussian_slopes(
        total_duration=duration,
        num_segments=segments,
        amplitude=A,
        mean=mu,
        std_dev=sigma
    )
    
    # --- List all the coefficients ---
    print("Gaussian Pulse Coefficients:")
    print(f"Amplitude (A): {A}")
    print(f"Mean (μ): {mu}")
    print(f"Standard Deviation (σ): {sigma}")
    print("-" * 30)
    print(f"Number of segments: {segments}")
    
    # --- Plot the results ---
    plot_gaussian_pulse(time_points, duration, segments, A, mu, sigma)

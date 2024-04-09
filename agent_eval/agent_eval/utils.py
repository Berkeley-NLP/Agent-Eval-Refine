from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

def display_images(images):
    """Display list of PIL images in a 2xN grid."""
    n = len(images)
    
    # Calculate grid shape
    cols = int(np.ceil(n / 2.0))
    rows = 2 if n > 1 else 1
    cols, rows = rows, cols  # Swap

    # Create a grid of subplots
    fig, axs = plt.subplots(rows, cols, figsize=(20, 10))
    
    # If there's only one image, axs won't be a 2D array, so make it one for consistency
    if n == 1:
        axs = np.array([[axs]])
    elif n <= cols:
        axs = np.array([axs])

    # Display each image in its subplot
    for i, img in enumerate(images):
        row, col = divmod(i, cols)
        axs[row][col].imshow(img)
        axs[row][col].axis('off')  # Hide axes

    # For cases where the total number of images is odd, hide the last unused subplot
    if n % 2 == 1:
        axs[-1, -1].axis('off')

    plt.tight_layout()
    plt.show()

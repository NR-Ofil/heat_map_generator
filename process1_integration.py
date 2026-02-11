"""
Process 1: Long integration on red color detection.
Creates and saves a cumulative matrix with cumulative values.
"""

import cv2
import numpy as np
from pathlib import Path
import config
from video_processor import (
    process_video,
    remove_persistent_pixels
)


def create_cumulative_matrix(video_path: str) -> np.ndarray:
    """
    Process video and create cumulative matrix of red pixel detections.
    
    Args:
        video_path: Path to input video file
        
    Returns:
        Cumulative matrix (2D numpy array)
    """
    print(f"Processing video: {video_path}")
    
    # Process video and get accumulator
    acc, representative_frame, frames_processed, total_frames = process_video(video_path)
    
    # Remove persistent pixels (stuck/hot pixels)
    acc = remove_persistent_pixels(acc, frames_processed)
    
    print(f"\nIntegration complete!")
    print(f"  Frames processed: {frames_processed}/{total_frames}")
    print(f"  Matrix shape: {acc.shape}")
    print(f"  Matrix dtype: {acc.dtype}")
    print(f"  Min value: {acc.min():.2f}")
    print(f"  Max value: {acc.max():.2f}")
    print(f"  Mean value: {acc.mean():.2f}")
    
    return acc, representative_frame


def main():
    """Main entry point for Process 1."""
    # Focus on 2_insulators_4 folder
    folder_name = "Prisma"
    #folder_name = "2_insulators_4"
    video_folder = Path("results_for_users") / folder_name
    
    # Find video file in folder
    video_files = list(video_folder.glob("*.mov"))
    if not video_files:
        print(f"Error: No .mov file found in {video_folder}")
        return
    
    video_path = video_files[0]
    print(f"Found video: {video_path.name}\n")
    
    # Create cumulative matrix
    acc, representative_frame = create_cumulative_matrix(str(video_path))
    
    # Save cumulative matrix and representative frame
    matrix_file = video_folder / "cumulative_matrix.npy"
    frame_file = video_folder / "representative_frame.npy"
    
    np.save(str(matrix_file), acc)
    np.save(str(frame_file), representative_frame)
    
    print(f"\nSaved:")
    print(f"  Cumulative matrix: {matrix_file}")
    print(f"  Representative frame: {frame_file}")
    print(f"\nYou can now run Process 2 to create interactive overlay.")


if __name__ == "__main__":
    main()


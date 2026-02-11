"""
Video processing utilities for red-spot heatmap generation.
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import config


def create_kernel(size: int = None) -> np.ndarray:
    """Create morphological kernel for noise reduction."""
    if size is None:
        size = config.KERNEL_SIZE
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))


def detect_red_pixels(frame: np.ndarray) -> np.ndarray:
    """
    Detect red pixels in a frame using HSV color space.
    
    Args:
        frame: BGR frame from video
        
    Returns:
        Binary mask where red pixels are white (255)
    """
    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Two bands for red (wraps around 0/180)
    mask1 = cv2.inRange(hsv, config.LOWER_RED_1, config.UPPER_RED_1)
    mask2 = cv2.inRange(hsv, config.LOWER_RED_2, config.UPPER_RED_2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    # Clean small speckles
    kernel = create_kernel()
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=1)
    
    return mask


def process_video(video_path: str) -> Tuple[np.ndarray, np.ndarray, int, int]:
    """
    Process video and accumulate red pixel detections.
    
    Args:
        video_path: Path to input video file
        
    Returns:
        Tuple of (accumulator, representative_frame, frames_processed, total_frames)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video at '{video_path}'")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    acc = np.zeros((height, width), dtype=np.float32)
    representative_frame = None
    
    frame_idx = 0
    used = 0
    
    print(f"Processing video: {video_path}")
    print(f"Total frames: {total_frames}, Processing every {config.FRAME_STRIDE} frame(s)")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_idx % config.FRAME_STRIDE != 0:
            frame_idx += 1
            continue
        
        if representative_frame is None:
            representative_frame = frame.copy()
        
        # Detect red pixels
        mask = detect_red_pixels(frame)
        
        # Accumulate (normalize to 0..1 so stride doesn't affect scale)
        acc += (mask.astype(np.float32) / 255.0)
        used += 1
        frame_idx += 1
        
        if used % 100 == 0:
            print(f"  Processed {used} frames...")
    
    cap.release()
    
    if used == 0:
        raise RuntimeError("No frames processed. Check frame_stride or video file.")
    
    print(f"Completed: {used}/{total_frames} frames processed")
    return acc, representative_frame, used, total_frames


def remove_persistent_pixels(acc: np.ndarray, frames_processed: int) -> np.ndarray:
    """
    Remove pixels that are red in too many frames (likely stuck/hot pixels).
    
    Args:
        acc: Accumulator array
        frames_processed: Number of frames that were processed
        
    Returns:
        Accumulator with persistent pixels zeroed out
    """
    frac = acc / float(frames_processed)  # fraction of frames per pixel
    persistent_mask = (frac >= config.PERSISTENT_FRAC_THRESHOLD)
    acc[persistent_mask] = 0.0
    return acc


def create_heatmap(acc: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create heatmap visualization from accumulator.
    
    Args:
        acc: Accumulator array
        
    Returns:
        Tuple of (heatmap_bgr, acc_u8) where heatmap_bgr is the colored heatmap
        and acc_u8 is the normalized uint8 version
    """
    # Optional blur to smooth blockiness
    acc_blur = cv2.GaussianBlur(acc, (0, 0), sigmaX=config.BLUR_SIGMA, sigmaY=config.BLUR_SIGMA)
    
    # Normalize to 0..255 for colormap
    acc_norm = cv2.normalize(acc_blur, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    acc_u8 = acc_norm.astype(np.uint8)
    
    # Map colormap name to OpenCV constant
    colormap_dict = {
        "JET": cv2.COLORMAP_JET,
        "HOT": cv2.COLORMAP_HOT,
        "PLASMA": cv2.COLORMAP_PLASMA,
        "VIRIDIS": cv2.COLORMAP_VIRIDIS,
    }
    colormap = colormap_dict.get(config.COLORMAP.upper(), cv2.COLORMAP_JET)
    
    # Apply colormap
    heatmap_bgr = cv2.applyColorMap(acc_u8, colormap)
    
    return heatmap_bgr, acc_u8


def create_overlay(base_frame: np.ndarray, heatmap_bgr: np.ndarray, acc_u8: np.ndarray) -> np.ndarray:
    """
    Create overlay of heatmap on representative frame.
    
    Args:
        base_frame: Representative frame from video
        heatmap_bgr: Colored heatmap
        acc_u8: Normalized accumulator (uint8)
        
    Returns:
        Blended overlay image
    """
    base = base_frame.copy()
    
    # Keep only strong hotspots in overlay
    mask_hot = (acc_u8 >= config.THRESHOLD_PCT).astype(np.uint8)[:, :, None]  # shape (H,W,1)
    
    # Blend heatmap with base
    blended = cv2.addWeighted(base, 1.0 - config.OVERLAY_ALPHA, heatmap_bgr, config.OVERLAY_ALPHA, 0.0)
    
    # Final overlay: only show blended where mask_hot == 1, otherwise keep base
    overlay = base * (1 - mask_hot) + blended * mask_hot
    
    return overlay


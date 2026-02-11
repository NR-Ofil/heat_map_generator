"""
Main script for processing video files and generating red-spot heatmaps.
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import os
import sys
import config
from video_processor import (
    process_video,
    remove_persistent_pixels,
    create_heatmap,
    create_overlay
)


def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    output_dir = Path(config.OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)
    return output_dir


def process_single_video(video_path: str, output_dir: Path) -> dict:
    """
    Process a single video file and generate heatmap outputs.
    
    Args:
        video_path: Path to input video file
        output_dir: Directory to save output files
        
    Returns:
        Dictionary with output file paths
    """
    video_name = Path(video_path).stem
    
    # Create subfolder for this video
    video_output_dir = output_dir / video_name
    video_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process video
    acc, representative_frame, frames_processed, total_frames = process_video(video_path)
    
    # Remove persistent pixels
    acc = remove_persistent_pixels(acc, frames_processed)
    
    # Create heatmap
    heatmap_bgr, acc_u8 = create_heatmap(acc)
    
    # Generate output file paths (simpler names in subfolder)
    heatmap_png = video_output_dir / "heatmap.png"
    heatmap_overlay_png = video_output_dir / "overlay.png"
    transparent_heat_png = video_output_dir / "transparent.png"
    
    # Save standalone heatmap
    cv2.imwrite(str(heatmap_png), heatmap_bgr)
    
    # Create and save overlay
    overlay = create_overlay(representative_frame, heatmap_bgr, acc_u8)
    cv2.imwrite(str(heatmap_overlay_png), overlay)
    
    # Create transparent PNG
    heat_rgb = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB)
    alpha = (acc_u8.astype(np.float32) / 255.0)
    alpha = np.clip(alpha, 0, 1)
    alpha = (alpha * 255).astype(np.uint8)
    heat_rgba = np.dstack([heat_rgb, alpha])
    Image.fromarray(heat_rgba).save(str(transparent_heat_png))
    
    return {
        "video": video_path,
        "frames_processed": frames_processed,
        "total_frames": total_frames,
        "output_folder": str(video_output_dir),
        "heatmap": str(heatmap_png),
        "overlay": str(heatmap_overlay_png),
        "transparent": str(transparent_heat_png)
    }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate red-spot heatmaps from video files"
    )
    parser.add_argument(
        "video",
        nargs="?",
        help="Path to video file (if not provided, processes all .mov files in current directory)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all .mov files in current directory"
    )
    
    args = parser.parse_args()
    
    output_dir = ensure_output_dir()
    
    if args.all or args.video is None:
        # Process all .mov files in current directory
        video_files = list(Path(".").glob("*.mov"))
        if not video_files:
            print("No .mov files found in current directory.")
            sys.exit(1)
        
        print(f"Found {len(video_files)} video file(s) to process\n")
        results = []
        
        for video_path in sorted(video_files):
            try:
                print(f"\n{'='*60}")
                result = process_single_video(str(video_path), output_dir)
                results.append(result)
                print(f"\nSaved outputs for {video_path.name}:")
                print(f"  Output folder:      {result['output_folder']}")
                print(f"    - heatmap.png")
                print(f"    - overlay.png")
                print(f"    - transparent.png")
            except Exception as e:
                print(f"Error processing {video_path}: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"\nProcessing complete! Processed {len(results)} video(s).")
        print(f"All outputs saved to: {output_dir}")
        
    else:
        # Process single video
        video_path = Path(args.video)
        if not video_path.exists():
            print(f"Error: Video file not found: {video_path}")
            sys.exit(1)
        
        try:
            result = process_single_video(str(video_path), output_dir)
            print(f"\nFrames processed: {result['frames_processed']}/{result['total_frames']}")
            print("\nSaved:")
            print(f"  Output folder:      {result['output_folder']}")
            print(f"    - heatmap.png")
            print(f"    - overlay.png")
            print(f"    - transparent.png")
        except Exception as e:
            print(f"Error processing video: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Script to create the fabric folder structure for organizing images.
This creates the base folder structure for fabrics and their components.
"""

import os
import sys

# Base path where fabric structure will be created
BASE_PATH = "fabrics"

# Define the structure
FABRIC_TYPES = ["cotton", "silk", "linen", "polyester", "wool"]
COLORS = ["white", "black", "blue", "beige", "navy", "gray", "brown"]

# Parts that need style folders
PARTS_WITH_STYLES = {
    "collar": 3,       # 3 styles
    "sleeves": 3,      # 3 styles (left+right in one image)
    "pocket": 3,       # 3 styles
    "button": 3,       # 3 styles
}

# Parts without style folders (direct image)
PARTS_WITHOUT_STYLES = ["button_strip", "body"]


def create_folder_structure(base_path=BASE_PATH):
    """
    Create the complete fabric folder structure.

    Structure:
    fabrics/
    ├── {fabric_type}/
    │   └── {color}/
    │       ├── collar/
    │       │   └── style_X/
    │       │       ├── cover.png
    │       │       └── option.png
    │       ├── sleeves/
    │       │   └── style_X/
    │       │       ├── cover.png
    │       │       └── option.png
    │       ├── pocket/
    │       │   └── style_X/
    │       │       ├── cover.png
    │       │       └── option.png
    │       ├── button/
    │       │   └── style_X/
    │       │       ├── cover.png
    │       │       └── option.png
    │       ├── button_strip/
    │       │   └── cover.png (direct, no folder)
    │       └── body/
    │           └── cover.png (direct, no folder)
    """

    print(f"Creating fabric folder structure at: {os.path.abspath(base_path)}")
    print("=" * 70)

    # Create base folder
    os.makedirs(base_path, exist_ok=True)

    total_folders = 0
    total_placeholders = 0

    for fabric_type in FABRIC_TYPES:
        fabric_path = os.path.join(base_path, fabric_type)
        os.makedirs(fabric_path, exist_ok=True)
        total_folders += 1
        print(f"\n✓ Created: {fabric_type}/")

        for color in COLORS:
            color_path = os.path.join(fabric_path, color)
            os.makedirs(color_path, exist_ok=True)
            total_folders += 1
            print(f"  ✓ Created: {fabric_type}/{color}/")

            # Create parts with style folders
            for part_name, num_styles in PARTS_WITH_STYLES.items():
                part_path = os.path.join(color_path, part_name)
                os.makedirs(part_path, exist_ok=True)
                total_folders += 1

                for style_num in range(1, num_styles + 1):
                    style_folder = f"style_{style_num}"
                    style_path = os.path.join(part_path, style_folder)
                    os.makedirs(style_path, exist_ok=True)
                    total_folders += 1

                    # Create placeholder files
                    cover_file = os.path.join(style_path, "cover.png")
                    option_file = os.path.join(style_path, "option.png")

                    # Create .gitkeep to preserve empty folders
                    with open(os.path.join(style_path, ".gitkeep"), 'w') as f:
                        f.write("")

                    total_placeholders += 2
                    print(f"    ✓ {part_name}/{style_folder}/ (cover.png + option.png)")

            # Create parts without style folders (direct image)
            for part_name in PARTS_WITHOUT_STYLES:
                part_path = os.path.join(color_path, part_name)
                os.makedirs(part_path, exist_ok=True)
                total_folders += 1

                # Create .gitkeep to preserve empty folder
                with open(os.path.join(part_path, ".gitkeep"), 'w') as f:
                    f.write("")

                total_placeholders += 1
                print(f"    ✓ {part_name}/ (cover.png only)")

    print("\n" + "=" * 70)
    print(f"✅ Folder structure created successfully!")
    print(f"   Total folders created: {total_folders}")
    print(f"   Total image placeholders: {total_placeholders}")
    print(f"\n📁 Location: {os.path.abspath(base_path)}")
    print("\n📋 Next steps:")
    print("   1. Upload images to respective folders")
    print("   2. Use the folder paths in your Django models")
    print("   3. Configure Cloudinary to mirror this structure")


def create_sample_structure():
    """Create a smaller sample structure for testing."""
    print("Creating SAMPLE structure (1 fabric type, 2 colors)...")
    print("=" * 70)

    sample_path = "fabrics_sample"
    os.makedirs(sample_path, exist_ok=True)

    # Just create cotton with white and black
    for fabric_type in ["cotton"]:
        fabric_path = os.path.join(sample_path, fabric_type)

        for color in ["white", "black"]:
            color_path = os.path.join(fabric_path, color)
            os.makedirs(color_path, exist_ok=True)

            # Create parts with style folders
            for part_name, num_styles in PARTS_WITH_STYLES.items():
                part_path = os.path.join(color_path, part_name)

                for style_num in range(1, num_styles + 1):
                    style_folder = f"style_{style_num}"
                    style_path = os.path.join(part_path, style_folder)
                    os.makedirs(style_path, exist_ok=True)

                    with open(os.path.join(style_path, ".gitkeep"), 'w') as f:
                        f.write("")

            # Create parts without style folders
            for part_name in PARTS_WITHOUT_STYLES:
                part_path = os.path.join(color_path, part_name)
                os.makedirs(part_path, exist_ok=True)

                with open(os.path.join(part_path, ".gitkeep"), 'w') as f:
                    f.write("")

    print(f"✅ Sample structure created at: {os.path.abspath(sample_path)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create fabric folder structure")
    parser.add_argument(
        '--sample',
        action='store_true',
        help='Create a small sample structure for testing'
    )
    parser.add_argument(
        '--path',
        type=str,
        default=BASE_PATH,
        help='Base path where structure will be created (default: fabrics)'
    )

    args = parser.parse_args()

    if args.sample:
        create_sample_structure()
    else:
        create_folder_structure(args.path)

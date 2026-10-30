import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

FRESHNESS_DIR = r"C:\Users\sumit\.gemini\antigravity\scratch\food-verse-ai\backend\data\freshness_samples"
HYGIENE_DIR = r"C:\Users\sumit\.gemini\antigravity\scratch\food-verse-ai\backend\data\hygiene_samples"

os.makedirs(FRESHNESS_DIR, exist_ok=True)
os.makedirs(HYGIENE_DIR, exist_ok=True)

# 1. Generate Freshness Sample Images
def create_freshness_image(filename, produce_name, bg_color, base_color, spots, wrinkles, blur=False):
    width, height = 500, 400
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Fruit body
    draw.ellipse([100, 70, 400, 330], fill=base_color, outline="#1E293B", width=3)

    # Stem / leaf
    draw.rectangle([240, 45, 260, 80], fill="#78350F")
    draw.ellipse([250, 40, 290, 65], fill="#16A34A")

    # Add spots / bruising if applicable
    for s in spots:
        draw.ellipse([s[0], s[1], s[0]+s[2], s[1]+s[3]], fill=s[4])

    # Add wrinkling lines if applicable
    for w in wrinkles:
        draw.line(w, fill="#78350F", width=2)

    # Header and footer
    draw.rectangle([0, 0, width, 45], fill="#0F172A")
    draw.text((15, 14), f"FOOD VERSE AI  |  FRESHNESS: {produce_name.upper()}", fill="#F8FAFC")
    draw.rectangle([0, 360, width, height], fill="#1E293B")
    draw.text((15, 372), f"Visual Surface Inspection Sample", fill="#94A3B8")

    if blur:
        # Heavily blur to trigger blur detection check
        cv_img = np.array(img)
        blurred = cv2.GaussianBlur(cv_img, (35, 35), 0)
        img = Image.fromarray(blurred)

    save_path = os.path.join(FRESHNESS_DIR, filename)
    img.save(save_path, "JPEG", quality=90)
    print(f"Created freshness sample: {save_path}")

# Fresh Apple
create_freshness_image(
    "fresh_apple.jpg",
    "Honeycrisp Apple (Optimal Quality)",
    "#FEF2F2",
    "#DC2626",
    [],
    []
)

# Bruised Banana
create_freshness_image(
    "bruised_banana.jpg",
    "Cavendish Banana (Moderate Quality)",
    "#FEFCE8",
    "#FACC15",
    [
        (160, 140, 35, 30, "#713F12"),
        (220, 210, 45, 35, "#713F12"),
        (310, 170, 25, 25, "#713F12"),
        (260, 260, 40, 25, "#854D0E"),
    ],
    []
)

# Stale Tomato
create_freshness_image(
    "stale_tomato.jpg",
    "Stale Vine Tomato (Visibly Degraded)",
    "#FFF1F2",
    "#B91C1C",
    [
        (140, 120, 50, 45, "#451A03"),
        (280, 200, 65, 55, "#451A03"),
        (200, 230, 45, 40, "#581C87"),
    ],
    [
        [(150, 160), (220, 170)],
        [(170, 210), (240, 225)],
        [(250, 140), (330, 165)],
        [(260, 240), (340, 260)],
    ]
)

# Uncertain Leafy Greens (low contrast / blurred)
create_freshness_image(
    "uncertain_greens.jpg",
    "Leafy Greens (Uncertain / Low Evidence)",
    "#F0FDF4",
    "#22C55E",
    [],
    [],
    blur=True
)


# 2. Generate Hygiene Sample Images
def create_hygiene_image(filename, title, is_clean):
    width, height = 640, 480
    img = Image.new("RGB", (width, height), color="#1E293B")
    draw = ImageDraw.Draw(img)

    # Kitchen floor & wall
    draw.rectangle([0, 0, width, 240], fill="#334155")
    draw.rectangle([0, 240, width, height], fill="#0F172A")

    # Stainless steel prep table
    draw.rectangle([80, 220, 560, 380], fill="#94A3B8", outline="#CBD5E1", width=3)
    draw.line([(80, 220), (560, 220)], fill="#F8FAFC", width=2)
    # Table legs
    draw.rectangle([90, 380, 110, 460], fill="#64748B")
    draw.rectangle([530, 380, 550, 460], fill="#64748B")

    if is_clean:
        # Covered containers with lids
        draw.rectangle([130, 180, 240, 220], fill="#0284C7", outline="#E2E8F0", width=2)
        draw.text((145, 195), "SEALED PAN", fill="#FFFFFF")
        draw.rectangle([280, 170, 390, 220], fill="#0284C7", outline="#E2E8F0", width=2)
        draw.text((295, 190), "LID SECURE", fill="#FFFFFF")
        
        # Trash bin positioned far away with closed lid
        draw.rectangle([20, 320, 70, 420], fill="#475569", outline="#059669", width=2)
        draw.text((25, 360), "TRASH", fill="#F8FAFC")
        
        # Protective badge
        draw.rectangle([430, 150, 530, 220], fill="#065F46")
        draw.text((440, 175), "GLOVES ON", fill="#34D399")
    else:
        # Violation: Open uncovered pan with spills
        draw.rectangle([130, 180, 250, 220], fill="#EA580C", outline="#EF4444", width=3)
        draw.text((140, 195), "UNCOVERED", fill="#FFFFFF")
        # Spill on counter
        draw.ellipse([210, 230, 310, 260], fill="#DC2626")
        draw.text((230, 240), "SPILL", fill="#FFFFFF")

        # Trash bin placed directly against prep table (proximity hazard)
        draw.rectangle([470, 240, 550, 370], fill="#7F1D1D", outline="#EF4444", width=3)
        draw.text((485, 290), "OPEN BIN", fill="#FEF2F2")

        # Clutter / multiple loose utensils
        draw.line([(320, 250), (410, 270)], fill="#F59E0B", width=4)
        draw.line([(350, 240), (420, 290)], fill="#F59E0B", width=4)
        draw.line([(330, 280), (400, 260)], fill="#F59E0B", width=4)

    # Header banner
    draw.rectangle([0, 0, width, 50], fill="#0B0F17")
    draw.text((20, 16), f"KITCHENGUARD AUDIT  |  {title.upper()}", fill="#F8FAFC")
    draw.text((500, 18), "PART 2 AI CV", fill="#38BDF8")

    save_path = os.path.join(HYGIENE_DIR, filename)
    img.save(save_path, "JPEG", quality=90)
    print(f"Created hygiene sample image: {save_path}")

create_hygiene_image("clean_kitchen.jpg", "Compliant Commercial Prep Station", True)
create_hygiene_image("violation_kitchen.jpg", "Flagged Hygiene Violations Station", False)


# 3. Generate Valid Sample MP4 Kitchen Video
def create_sample_video(filename, duration_sec=3.0, fps=10):
    save_path = os.path.join(HYGIENE_DIR, filename)
    width, height = 480, 360
    total_frames = int(duration_sec * fps)

    # Use mp4v or XVID fourcc
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(save_path, fourcc, fps, (width, height))

    if not out.isOpened():
        print(f"Failed to open VideoWriter for {save_path}, trying XVID...")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(save_path, fourcc, fps, (width, height))

    for i in range(total_frames):
        sec = i / fps
        frame = np.full((height, width, 3), 35, dtype=np.uint8)
        
        # Counter line
        cv2.rectangle(frame, (40, 160), (440, 280), (120, 120, 120), -1)
        cv2.rectangle(frame, (40, 160), (440, 280), (200, 200, 200), 2)

        # Draw a moving container or hand
        pos_x = int(60 + (i * 12) % 320)
        cv2.rectangle(frame, (pos_x, 140), (pos_x + 60, 180), (0, 165, 255), -1)
        cv2.putText(frame, "PREP", (pos_x + 8, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        # Trash bin
        cv2.rectangle(frame, (380, 200), (430, 270), (0, 0, 180), -1)
        cv2.putText(frame, "BIN", (390, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # Header overlay
        cv2.rectangle(frame, (0, 0), (width, 40), (15, 15, 15), -1)
        time_text = f"KITCHEN MONITOR - TIME: 00:{int(sec):02d} (FRAME {i+1}/{total_frames})"
        cv2.putText(frame, time_text, (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 200), 1)

        out.write(frame)

    out.release()
    print(f"Created sample hygiene video: {save_path} ({duration_sec}s, {total_frames} frames)")

create_sample_video("kitchen_prep_clip.mp4", duration_sec=3.0, fps=10)

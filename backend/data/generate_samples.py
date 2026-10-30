import os
from PIL import Image, ImageDraw, ImageFont

def create_food_image(filename, title, subtitle, bg_color, accent_color, shapes):
    width, height = 600, 450
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Draw gradient or styled background circles / plates
    draw.ellipse([80, 50, 520, 410], fill="#FFFFFF", outline="#E2E8F0", width=4)
    draw.ellipse([100, 70, 500, 390], fill=accent_color)

    # Draw customized shapes representing the food
    for shape in shapes:
        stype = shape.get("type")
        coords = shape.get("coords")
        color = shape.get("color")
        outline = shape.get("outline", None)
        width_ol = shape.get("width", 1)
        if stype == "ellipse":
            draw.ellipse(coords, fill=color, outline=outline, width=width_ol)
        elif stype == "rectangle":
            draw.rectangle(coords, fill=color, outline=outline, width=width_ol)
        elif stype == "polygon":
            draw.polygon(coords, fill=color, outline=outline)

    # Plate rim highlights
    draw.arc([105, 75, 495, 385], start=0, end=360, fill="#FFFFFF", width=2)

    # Top banner with Food Verse AI label
    draw.rectangle([0, 0, width, 55], fill="#0F172A")
    draw.text((20, 16), f"FOOD VERSE AI  |  SAMPLE: {title.upper()}", fill="#F8FAFC")
    draw.text((450, 18), "PART 1 DEMO", fill="#38BDF8")

    # Bottom badge
    draw.rectangle([0, 400, width, height], fill="#1E293B")
    draw.text((25, 415), f"{title} - {subtitle}", fill="#CBD5E1")

    dir_path = r"C:\Users\sumit\.gemini\antigravity\scratch\food-verse-ai\backend\data\sample_images"
    os.makedirs(dir_path, exist_ok=True)
    full_path = os.path.join(dir_path, filename)
    img.save(full_path, "JPEG", quality=90)
    print(f"Generated sample image: {full_path}")

# 1. Avocado Toast
create_food_image(
    "avocado_toast.jpg",
    "Avocado Toast",
    "Artisanal whole wheat sourdough with smashed avocado & red chili",
    "#FEF3C7",
    "#D97706",
    [
        {"type": "rectangle", "coords": [180, 160, 420, 300], "color": "#B45309", "outline": "#78350F", "width": 4},
        {"type": "rectangle", "coords": [190, 170, 410, 290], "color": "#FBBF24"},
        {"type": "ellipse", "coords": [200, 180, 400, 280], "color": "#65A30D"},
        {"type": "ellipse", "coords": [240, 210, 360, 260], "color": "#4D7C0F"},
        {"type": "ellipse", "coords": [250, 220, 265, 235], "color": "#EF4444"},
        {"type": "ellipse", "coords": [330, 230, 345, 245], "color": "#EF4444"},
        {"type": "ellipse", "coords": [290, 240, 305, 255], "color": "#EF4444"},
    ]
)

# 2. Grilled Salmon Bowl
create_food_image(
    "grilled_salmon.jpg",
    "Grilled Salmon Bowl",
    "Atlantic salmon with brown rice & steamed broccoli florets",
    "#EFF6FF",
    "#E0F2FE",
    [
        # Rice base
        {"type": "ellipse", "coords": [160, 180, 320, 320], "color": "#FEF3C7"},
        # Salmon fillet
        {"type": "polygon", "coords": [(280, 140), (440, 210), (390, 310), (240, 230)], "color": "#FB923C", "outline": "#EA580C"},
        {"type": "rectangle", "coords": [290, 200, 400, 210], "color": "#9A3412"},
        {"type": "rectangle", "coords": [310, 230, 380, 240], "color": "#9A3412"},
        # Broccoli
        {"type": "ellipse", "coords": [180, 150, 250, 220], "color": "#15803D"},
        {"type": "ellipse", "coords": [220, 140, 280, 190], "color": "#166534"},
        {"type": "ellipse", "coords": [160, 210, 220, 270], "color": "#15803D"},
    ]
)

# 3. Margherita Pizza
create_food_image(
    "margherita_pizza.jpg",
    "Margherita Pizza",
    "Crisp crust, San Marzano tomato, fresh mozzarella & fresh basil",
    "#FFF7ED",
    "#FED7AA",
    [
        # Crust
        {"type": "ellipse", "coords": [150, 120, 450, 360], "color": "#D97706", "outline": "#B45309", "width": 6},
        # Sauce
        {"type": "ellipse", "coords": [170, 140, 430, 340], "color": "#DC2626"},
        # Mozzarella splotches
        {"type": "ellipse", "coords": [200, 180, 260, 230], "color": "#FEF08A"},
        {"type": "ellipse", "coords": [320, 170, 390, 220], "color": "#FEF08A"},
        {"type": "ellipse", "coords": [230, 260, 310, 310], "color": "#FEF08A"},
        {"type": "ellipse", "coords": [340, 250, 400, 290], "color": "#FEF08A"},
        # Basil leaves
        {"type": "ellipse", "coords": [270, 200, 300, 225], "color": "#15803D"},
        {"type": "ellipse", "coords": [215, 240, 240, 260], "color": "#15803D"},
        {"type": "ellipse", "coords": [310, 240, 335, 260], "color": "#15803D"},
    ]
)

# 4. Berry Oatmeal Bowl
create_food_image(
    "berry_oatmeal.jpg",
    "Berry Oatmeal Bowl",
    "Creamy rolled oats topped with blueberries, strawberries & almonds",
    "#F5F3FF",
    "#DDD6FE",
    [
        # Oatmeal base
        {"type": "ellipse", "coords": [160, 130, 440, 350], "color": "#FDE68A", "outline": "#D97706", "width": 4},
        # Blueberries
        {"type": "ellipse", "coords": [210, 190, 240, 220], "color": "#312E81"},
        {"type": "ellipse", "coords": [230, 230, 260, 260], "color": "#312E81"},
        {"type": "ellipse", "coords": [270, 170, 300, 200], "color": "#312E81"},
        {"type": "ellipse", "coords": [350, 250, 380, 280], "color": "#312E81"},
        # Strawberries
        {"type": "polygon", "coords": [(310, 200), (360, 220), (330, 270)], "color": "#EF4444"},
        {"type": "polygon", "coords": [(240, 260), (280, 280), (260, 320)], "color": "#EF4444"},
    ]
)

# 5. Chicken Caesar Salad
create_food_image(
    "chicken_caesar_salad.jpg",
    "Chicken Caesar Salad",
    "Crisp romaine lettuce, grilled chicken breast, parmesan & croutons",
    "#F0FDF4",
    "#DCFCE7",
    [
        # Greens bed
        {"type": "ellipse", "coords": [160, 130, 440, 350], "color": "#22C55E"},
        {"type": "ellipse", "coords": [180, 150, 300, 250], "color": "#16A34A"},
        {"type": "ellipse", "coords": [300, 200, 420, 320], "color": "#15803D"},
        # Grilled chicken strips
        {"type": "rectangle", "coords": [210, 190, 310, 220], "color": "#FDE047", "outline": "#CA8A04"},
        {"type": "rectangle", "coords": [270, 240, 370, 270], "color": "#FDE047", "outline": "#CA8A04"},
        # Croutons
        {"type": "rectangle", "coords": [330, 170, 360, 195], "color": "#B45309"},
        {"type": "rectangle", "coords": [200, 270, 230, 295], "color": "#B45309"},
        {"type": "rectangle", "coords": [280, 160, 305, 180], "color": "#B45309"},
    ]
)

# 6. Chocolate Cake
create_food_image(
    "chocolate_cake.jpg",
    "Chocolate Fudge Cake",
    "Rich layered dark chocolate sponge with decadent fudge frosting",
    "#FAF5FF",
    "#F3E8FF",
    [
        # Cake wedge
        {"type": "polygon", "coords": [(200, 320), (390, 330), (410, 170), (240, 160)], "color": "#451A03", "outline": "#1C1917", "width": 4},
        # Layers
        {"type": "polygon", "coords": [(205, 270), (395, 275), (400, 250), (210, 245)], "color": "#78350F"},
        {"type": "polygon", "coords": [(215, 210), (405, 215), (410, 170), (240, 160)], "color": "#291305"},
        # Cherry or berry on top
        {"type": "ellipse", "coords": [290, 130, 330, 170], "color": "#DC2626"},
    ]
)

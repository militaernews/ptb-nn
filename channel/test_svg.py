import svgwrite

# Define the TRANSLATIONS dictionary
TRANSLATIONS = {
    "GBAD": 10,
    "EW": 1,
    "Radar": 2,
    "C2": 4,
    "UAV": 66,
    "Marine": 4324,
    "Plane": 34,
    "Helicopter": 23543,
    "MLRS": 235532,
    "CSS": 2535,
    "Artillery": 434,
    "IFV": 42334,
    "APC": 4664,
    "AFV": 57,
    "ARV": 888,
    "TANK": 4355
}

# Function to create an SVG with images, numbers, and descriptions formatted correctly
def create_svg(blue_team, red_team, filename='output_styled_with_images.svg'):
    # Create an SVG drawing object with the same dimensions
    dwg = svgwrite.Drawing(filename, profile='tiny', size=("4400px", "3200px"))

    # Background gradient
    gradient = dwg.defs.add(dwg.linearGradient(start=(0, 0), end=(1, 0), id="bg_gradient"))
    gradient.add_stop_color(0, "#650000")
    gradient.add_stop_color(1, "#006464")

    # Apply background rectangle with the gradient
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="url(#bg_gradient)"))

    # Add background images if needed
    # Assuming paths or URLs to images are available, adjust the paths as per your image source
    # For example:
    # dwg.add(dwg.image('background_image_blue.png', insert=(0, 0), size=("2200px", "3200px")))
    # dwg.add(dwg.image('background_image_red.png', insert=(2200, 0), size=("2200px", "3200px")))

    # Title for the SVG
    dwg.add(dwg.text("Team Losses Overview", insert=(2200, 200), text_anchor="middle", font_size="80px", fill="white", font_family="Arial"))

    # Define positioning variables
    start_x_blue = 600
    start_x_red = 3000
    start_y = 400
    line_height = 160

    # Text formatting function (to position the number above the description)
    def add_team_stats(team_data, start_x, color):
        for idx, (desc, amount) in enumerate(team_data.items()):
            y = start_y + idx * line_height
            # Adding the number above
            dwg.add(dwg.text(f"{amount}", insert=(start_x, y), font_size="60px", fill=color, text_anchor="middle", font_family="Arial"))
            # Adding the description below
            dwg.add(dwg.text(f"{desc}", insert=(start_x, y + 60), font_size="45px", fill=color, text_anchor="middle", font_family="Arial"))

    # Draw BLUE Team data (left side)
    add_team_stats(blue_team, start_x_blue, "lightblue")

    # Draw RED Team data (right side)
    add_team_stats(red_team, start_x_red, "red")

    # Save the SVG to a file
    dwg.save()

# Example data for BLUE and RED teams
blue_team_data = TRANSLATIONS
red_team_data = {
    "GBAD": 15,
    "EW": 2,
    "Radar": 1,
    "C2": 7,
    "UAV": 50,
    "Marine": 4000,
    "Plane": 40,
    "Helicopter": 22000,
    "MLRS": 230000,
    "CSS": 2500,
    "Artillery": 500,
    "IFV": 42000,
    "APC": 4700,
    "AFV": 60,
    "ARV": 900,
    "TANK": 4400
}

# Generate the SVG with formatted text and background images
create_svg(blue_team_data, red_team_data, filename="team_losses_styled_with_images2.svg")




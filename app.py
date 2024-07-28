from flask import Flask, request, render_template, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import os
import base64
import json

app = Flask(__name__)

def b64encode(value):
    return base64.b64encode(value).decode('utf-8')

app.jinja_env.filters['b64encode'] = b64encode

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_images', methods=['POST'])
def process_images():
    files = request.files.getlist('images')
    image_data = []

    for file in files:
        img = Image.open(file.stream)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        img_data = {'name': file.filename, 'content': encoded_image}
        image_data.append(img_data)

    return render_template('sort_images.html', images=image_data)

@app.route('/generate_collage', methods=['POST'])
def generate_collage():
    try:
        positions = json.loads(request.form.get('positions'))
        titles = json.loads(request.form.get('titles'))
        autoresize = request.form.get('autoresize') == 'true'
        phone_placeholder = request.form.get('phone_placeholder') == 'true'
        arrangement = request.form.get('arrangement')

        # Debugging: Print positions and other details
        print("Positions:", positions)
        print("Positions Type:", type(positions))
        print("Titles:", titles)
        print("Autoresize:", autoresize)
        print("Phone Placeholder:", phone_placeholder)
        print("Arrangement:", arrangement)

        images = []
        for pos in positions:
            if isinstance(pos, list):
                pos = pos[0]  # Extract the single string element from the sublist
            img_content = base64.b64decode(request.form.getlist('images')[int(pos)-1])
            images.append(img_content)

        image_objects = [Image.open(io.BytesIO(img_content)).convert("RGBA") for img_content in images]

        if phone_placeholder:
            phone_placeholder_image = Image.open("phone_placeholder.png").convert("RGBA")
            screen_left, screen_upper, screen_right, screen_lower = 20, 35, 485, 1020
            screen_width, screen_height = screen_right - screen_left, screen_lower - screen_upper
            radius = 50
            mask = Image.new("L", (screen_width, screen_height), 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0, screen_width, screen_height), radius, fill=255)

            processed_images = []
            for img, title in zip(image_objects, titles):
                img = img.resize((screen_width, screen_height))
                img.putalpha(mask)
                combined = phone_placeholder_image.copy()
                combined.paste(img, (screen_left, screen_upper), img)
                processed_images.append((combined, title))
        else:
            processed_images = [(img, title) for img, title in zip(image_objects, titles)]

        collage_image = create_collage(processed_images, autoresize, arrangement)

        # Debugging: Check if collage_image is None
        if collage_image is None:
            print("Collage image is None!")
        else:
            print("Collage image created successfully.")

        buffer = io.BytesIO()
        collage_image.save(buffer, format="PNG")
        encoded_collage = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return render_template('download.html', image_data=encoded_collage)
    except Exception as e:
        print(f"Error occurred: {e}")
        return f"An error occurred: {e}", 500

def create_collage(images_with_titles, autoresize, arrangement):
    try:
        if not images_with_titles:
            print("No images with titles provided.")
            return None

        images = [img for img, _ in images_with_titles]
        if not images:
            print("No images processed correctly.")
            return None
        
        margin = 10
        padding = 40
        bottom_padding = 80  # Increased bottom padding for better spacing
        max_width = max(image.width for image in images)
        max_height = max(image.height for image in images)

        if autoresize:
            resized_images = [image.resize((max_width, max_height)) for image in images]
        else:
            resized_images = images

        try:
            font_path = "/Library/Fonts/Arial.ttf"
            if not os.path.exists(font_path):
                font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
            font = ImageFont.truetype(font_path, 200)
        except IOError:
            font = ImageFont.load_default()

        draw_dummy = ImageDraw.Draw(Image.new('RGB', (1, 1)))  # Create a dummy draw object for text measurement

        if arrangement == 'horizontal':
            total_width = sum(image.width for image in resized_images) + margin * (len(resized_images) - 1)
            collage = Image.new('RGB', (total_width + 2 * padding, max_height + 2 * padding + bottom_padding), 'white')
            draw = ImageDraw.Draw(collage)
            x_offset = padding
            for i, (image, title) in enumerate(zip(resized_images, [t[1] if isinstance(t, tuple) else t for t in images_with_titles])):
                collage.paste(image, (x_offset, padding))
                if isinstance(title, str) and title.strip():
                    text_bbox = draw_dummy.textbbox((0, 0), title, font=font)
                    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
                    text_x = x_offset + (image.width - text_width) // 2
                    text_y = padding + image.height + 10
                    draw.text((text_x, text_y), title, fill='black', font=font)
                x_offset += image.width + margin
        else:
            total_height = sum(image.height for image in resized_images) + margin * (len(resized_images) - 1) + bottom_padding * len(resized_images)
            collage = Image.new('RGB', (max_width + 2 * padding, total_height + 2 * padding), 'white')
            draw = ImageDraw.Draw(collage)
            y_offset = padding
            for i, (image, title) in enumerate(zip(resized_images, [t[1] if isinstance(t, tuple) else t for t in images_with_titles])):
                collage.paste(image, (padding, y_offset))
                if isinstance(title, str) and title.strip():
                    text_bbox = draw_dummy.textbbox((0, 0), title, font=font)
                    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
                    text_x = padding + (image.width - text_width) // 2
                    text_y = y_offset + image.height + 10
                    draw.text((text_x, text_y), title, fill='black', font=font)
                y_offset += image.height + margin + bottom_padding  # Add bottom padding for each image

        return collage
    except Exception as e:
        print(f"Error in create_collage: {e}")
        return None

if __name__ == "__main__":
    app.run(debug=True)

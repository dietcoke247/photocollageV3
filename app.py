from flask import Flask, request, render_template, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import os
import base64
import json

app = Flask(__name__)

# Custom filter to base64 encode image content
def b64encode(value):
    return base64.b64encode(value).decode('utf-8')

app.jinja_env.filters['b64encode'] = b64encode

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_images', methods=['POST'])
def process_images():
    images = request.files.getlist('images')

    image_data = []
    for img in images:
        img_data = {
            'name': img.filename,
            'content': img.read()
        }
        image_data.append(img_data)

    return render_template('sort_images.html', images=image_data)

from flask import Flask, request, render_template, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import os
import base64
import json

app = Flask(__name__)

# Custom filter to base64 encode image content
def b64encode(value):
    return base64.b64encode(value).decode('utf-8')

app.jinja_env.filters['b64encode'] = b64encode

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_images', methods=['POST'])
def process_images():
    images = request.files.getlist('images')

    image_data = []
    for img in images:
        img_data = {
            'name': img.filename,
            'content': img.read()
        }
        image_data.append(img_data)

    return render_template('sort_images.html', images=image_data)

@app.route('/generate_collage', methods=['POST'])
def generate_collage():
    positions = json.loads(request.form.get('positions'))
    titles = json.loads(request.form.get('titles'))
    autoresize = request.form.get('autoresize') == 'true'
    arrangement = request.form.get('arrangement')

    images = []
    for pos in positions:
        img_content = base64.b64decode(request.form.getlist('images')[int(pos[0])-1])
        images.append(img_content)

    image_objects = [Image.open(io.BytesIO(img_content)) for img_content in images]

    # Initialize max_width and max_height
    max_width = max(image.width for image in image_objects)
    max_height = max(image.height for image in image_objects)

    if autoresize:
        # Resize all images to the maximum dimensions
        resized_images = [image.resize((max_width, max_height)) for image in image_objects]
    else:
        resized_images = image_objects

    padding = 40
    margin = 20
    bottom_padding = 80  # Increased bottom padding for better spacing

    # Set up font for drawing text
    try:
        font_path = "/Library/Fonts/Arial.ttf"
        if not os.path.exists(font_path):
            font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
        font = ImageFont.truetype(font_path, 65)  # Increased font size by 30
    except IOError:
        font = ImageFont.load_default()

    draw_dummy = ImageDraw.Draw(Image.new('RGB', (1, 1)))  # Create a dummy draw object for text measurement

    if arrangement == 'horizontal':
        # Create a horizontal collage
        total_width = sum(image.width for image in resized_images) + margin * (len(resized_images) - 1)
        collage = Image.new('RGB', (total_width + 2 * padding, max_height + 2 * padding + bottom_padding), 'white')  # Set background to white
        draw = ImageDraw.Draw(collage)
        x_offset = padding
        for i, image in enumerate(resized_images):
            collage.paste(image, (x_offset, padding))
            text_width, text_height = draw_dummy.textbbox((0, 0), titles[i], font=font)[2:4]
            if autoresize:
                text_y = padding + max_height + 10  # Align text at the bottom of the largest image
            else:
                text_y = padding + image.height + 10  # Align text just below the image
            text_x = x_offset + (image.width - text_width) // 2
            draw.text((text_x, text_y), titles[i], fill='black', font=font)
            x_offset += image.width + margin
    else:
        # Create a vertical collage
        # Adjust total_height to account for text height and additional padding for each image
        total_height = sum(image.height for image in resized_images) + margin * (len(resized_images) - 1) + bottom_padding * len(resized_images)
        collage = Image.new('RGB', (max_width + 2 * padding, total_height + 2 * padding), 'white')  # Set background to white
        draw = ImageDraw.Draw(collage)
        y_offset = padding
        for i, image in enumerate(resized_images):
            collage.paste(image, (padding, y_offset))
            text_width, text_height = draw_dummy.textbbox((0, 0), titles[i], font=font)[2:4]
            if autoresize:
                text_y = y_offset + max_height + 10  # Align text at the bottom of the largest image
            else:
                text_y = y_offset + image.height + 10  # Align text just below the image
            text_x = padding + (image.width - text_width) // 2
            draw.text((text_x, text_y), titles[i], fill='black', font=font)
            y_offset += image.height + margin + bottom_padding  # Add bottom padding for each image

    # Save collage to a byte buffer
    buffer = io.BytesIO()
    collage.save(buffer, format='PNG')
    buffer.seek(0)

    # Encode collage in base64
    collage_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return render_template('download.html', image_data=collage_base64)






if __name__ == '__main__':
    app.run(debug=True)

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

    images = []
    for pos in positions:
        img_content = base64.b64decode(request.form.getlist('images')[int(pos[0])-1])
        images.append(img_content)

    image_objects = [Image.open(io.BytesIO(img_content)) for img_content in images]

    margin = 10
    padding = 40
    max_width = sum(img.width for img in image_objects) + margin * (len(image_objects) - 1)
    max_height = max(img.height for img in image_objects) + padding + 30

    collage = Image.new('RGB', (max_width + 2 * padding, max_height + 2 * padding), 'white')
    draw = ImageDraw.Draw(collage)

    try:
        font_path = "/Library/Fonts/Arial.ttf"
        if not os.path.exists(font_path):
            font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
        font = ImageFont.truetype(font_path, 35)
    except IOError:
        font = ImageFont.load_default()

    current_x = padding

    for i, img in enumerate(image_objects):
        collage.paste(img, (current_x, padding))
        if titles[i]:  # Only draw text if it's not empty
            text_bbox = draw.textbbox((0, 0), titles[i], font=font)
            text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
            text_x = current_x + (img.width - text_width) // 2
            text_y = padding + img.height + 10
            draw.text((text_x, text_y), titles[i], fill="black", font=font)
        current_x += img.width + margin

    output = io.BytesIO()
    collage.save(output, format='PNG')
    output.seek(0)

    return render_template('download.html', image_data=base64.b64encode(output.getvalue()).decode('utf-8'))

if __name__ == "__main__":
    app.run(debug=True)

import uuid
import os
from preprocess import EnhanceImage
from flask import Flask, request, jsonify, make_response, redirect, url_for
# Initialize Flask app
app = Flask(__name__, static_folder='./static')

# Create an application context
app_ctx = app.app_context()
app_ctx.push()

from flask_swagger_ui import get_swaggerui_blueprint
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import DevConfig, ProdConfig

from werkzeug.utils import secure_filename
from PIL import Image


env = os.getenv('ENV', 'dev')
if env == 'dev':
    config = DevConfig()
elif env == 'prod':
    config = ProdConfig()
else:
    raise ValueError('Invalid environment')

app.config['DEBUG'] = config.DEBUG
app.config['NER_MODEL_PATH'] = config.NER_MODEL_PATH

with app.app_context():
    from ocr import ExtractTextFromImage
    from ner import ExtractEntities
    from response import GenerateResponse

# Configure limiter with global limit of 1000 requests per day
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["500 per day", "50 per hour"]
)

SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'  # Assuming swagger.json is in static folder

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "AI Powered ID Data Extraction API"
    }
    
)

app.register_blueprint(swaggerui_blueprint)

# Define allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Define allowed image extensions based on magic numbers
ALLOWED_MIME_TYPES = {
    'image/png': b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A',
    'image/jpeg': b'\xFF\xD8\xFF'
}

from functools import wraps
from flask import request, jsonify

api_keys = {'user1': 'Z8gsUAJZyMef5WZR-rSLvw'}

def authenticate_api_key(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if api_key not in api_keys.values():
            return jsonify({'error': 'Invalid API key'}), 401
        return func(*args, **kwargs)
    return decorated_function

# Function to check allowed file extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@limiter.exempt
def redirect_to_docs():
    return redirect(url_for('swagger_ui.show'))  

@app.route('/api/v1/extract-data-from-image', methods=['POST'])
@authenticate_api_key
@limiter.limit("500/day;50/hour")
def upload_image():
    # Check if request has a file part
    # print(request.data[:10])
    if 'image' not in request.files and not request.data:
        response = make_response(jsonify({'error': 'No image data found'}), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

    filename = ''

    # Check if image data is in request.files (fallback for compatibility)
    if 'image' in request.files:
        file = request.files['image']
        # Check if user selected a file
        if file.filename == '':
            response = make_response(jsonify({'error': 'No selected file'}), 400)
            response.headers['Content-Type'] = 'application/json'
            return response
        

        # Check allowed file extension
        if file and allowed_file(file.filename):
            # Generate unique filename using UUID
            filename = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
            # Create images directory if it doesn't exist
            if not os.path.isdir('images'):
                os.makedirs('images')
            filepath = os.path.join('images', filename)
            file.save(filepath)

            img = Image.open(filepath)  # Replace with your image path
        
            # Converting RGBA image to RGB
            # if img.mode == "RGB":
            #     print("Image has 3 channels (RGB)")
            # else:
            #     print("Image has", len(img.getbands()), "channels (not RGB)")
            
            #     img.load()
            #     background = Image.new("RGB", img.size, (255, 255, 255))
                
            #     background.paste(img, mask=img.split()[3])

            #     background.save(filepath, 'PNG', quality=100)
            enhancedImageFilePath = filepath

            if len(img.getbands()) > 3:
                print("Image has", len(img.getbands()), "channels (not RGB)")
                img.load()
                background = Image.new("RGB", img.size, (255, 255, 255))
                
                background.paste(img, mask=img.split()[3])

                background.save(filepath, 'PNG', quality=100)

                # Enhancing image
                enhancedImageFilePath = EnhanceImage(filepath)
            elif len(img.getbands()) == 3:
                print("Image has", len(img.getbands()), "channels (RGB)")
                enhancedImageFilePath = EnhanceImage(filepath)
            
            # Extracting text from image
            accumulated_text = ExtractTextFromImage(enhancedImageFilePath)
            
            # Extracting entities
            entities = ExtractEntities(accumulated_text)

            # Generating Response
            response = GenerateResponse(entities)


            response = make_response(jsonify(response), 201)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Extension not allowed
        response = make_response(jsonify({'error': 'File type not allowed'}), 415)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # Check if image data is in request.data (binary data)
    if request.data:
        image_data = request.data
        # Check image type using magic numbers
        image_type = None
        for mime_type, magic_number in ALLOWED_MIME_TYPES.items():
            if image_data.startswith(magic_number):
                image_type = mime_type
                break
        
        if not image_type:
            response = make_response(jsonify({'error': 'Unsupported image format'}), 415)
            response.headers['Content-Type'] = 'application/json'
            return response
        
        # Generate unique filename using UUID
        filename = f"{uuid.uuid4()}.{image_type.split('/')[1]}"
        # Create images directory if it doesn't exist
        if not os.path.isdir('images'):
            os.makedirs('images')
        filepath = os.path.join('images', filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_data)

        # img = Image.open(filepath)  # Replace with your image path
        
        # # Converting RGBA image to RGB
        # if img.mode == "RGB":
        #     print("Image has 3 channels (RGB)")
        # else:
        #     print("Image has", len(img.getbands()), "channels (not RGB)")
        
        #     img.load()
        #     background = Image.new("RGB", img.size, (255, 255, 255))
        #     background.paste(img, mask=img.split()[3])

        #     background.save(filepath, 'PNG', quality=100)
        
        enhancedImageFilePath = filepath

        if len(img.getbands()) > 3:
            print("Image has", len(img.getbands()), "channels (not RGB)")
            img.load()
            background = Image.new("RGB", img.size, (255, 255, 255))
            
            background.paste(img, mask=img.split()[3])

            background.save(filepath, 'PNG', quality=100)

            # Enhancing image
            enhancedImageFilePath = EnhanceImage(filepath)
        elif len(img.getbands()) == 3:
            print("Image has", len(img.getbands()), "channels (RGB)")
            enhancedImageFilePath = EnhanceImage(filepath)
        
        # Extracting text from image
        accumulated_text = ExtractTextFromImage(enhancedImageFilePath)
        
        # Extracting entities
        entities = ExtractEntities(accumulated_text)

        # Generating Response
        response = GenerateResponse(entities)

        response = make_response(jsonify(response), 201)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(jsonify({'error': 'Invalid image data format'}), 400)
        response.headers['Content-Type'] = 'application/json'
        return response 
    

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])

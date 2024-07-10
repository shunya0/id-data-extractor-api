import cv2, pytesseract, uuid, os
from PIL import Image
from preprocess import EnhancedImageGenerator

# Define allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Define allowed image extensions based on magic numbers
ALLOWED_MIME_TYPES = {
    'image/png': b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A',
    'image/jpeg': b'\xFF\xD8\xFF'
}

# Function to check allowed file extension
def AllowedFile(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ValidateImageType(image_data):
  """
  Checks the image type using magic numbers.

  Args:
      image_data: The raw image data from the request.

  Returns:
      The MIME type of the image or None if unsupported.
  """
  for mime_type, magic_number in ALLOWED_MIME_TYPES.items():
    if image_data.startswith(magic_number):
      return mime_type
  return None

def ValidateImageTypeFormData(image_data):
    """
    Checks the image type using magic numbers.

    Args:
        image_data: The raw image data from the request.

    Returns:
        The MIME type of the image or None if unsupported.
    """
    if image_data and AllowedFile(image_data.filename):
       return f"image/{image_data.filename.split('.')[-1]}"
    return None
       

def SaveAndPreprocessImage(image_data, image_type):
  """
  Saves the uploaded image data, generates a unique filename, and preprocesses it.

  Args:
      image_data: The raw image data from the request.
      image_type: The MIME type of the image.

  Returns:
      A tuple containing the filepath and the PIL image object (or None on error).
  """
  if not image_type:
    return None  # Handle unsupported image type

  filename = f"{uuid.uuid4()}.{image_type.split('/')[1]}"
  filepath = os.path.join('images', filename)
  os.makedirs('images', exist_ok=True)  # Create directory if it doesn't exist

  try:
    with open(filepath, 'wb') as f:
      f.write(image_data)
    img = Image.open(filepath)
    return filepath, img
  except Exception as e:
    print(f"Error saving image: {e}")
    return None

def SaveAndPreprocessImageFormData(image_data, image_type):
  """
  Saves the uploaded image data, generates a unique filename, and preprocesses it.

  Args:
      image_data: The raw image data from the request.
      image_type: The MIME type of the image.

  Returns:
      A tuple containing the filepath and the PIL image object (or None on error).
  """
  if not image_type:
    return None  # Handle unsupported image type

  filename = f"{uuid.uuid4()}.{image_type.split('/')[1]}"
  filepath = os.path.join('images', filename)
  os.makedirs('images', exist_ok=True)  # Create directory if it doesn't exist

  try:
    image_data.save(filepath)
    img = Image.open(filepath)
    return filepath, img
  except Exception as e:
    print(f"Error saving image: {e}")
    return None

def EnhancedImage(filepath):
  """
  Enhances the image (optional functionality).

  Args:
      filepath: Path to the image file.

  Returns:
      The filepath of the enhanced image (or the original filepath if enhancement fails).
  """
  try:
    img = Image.open(filepath)
    os.makedirs('result', exist_ok=True)
    if len(img.getbands()) > 3:
      print("Image has", len(img.getbands()), "channels (not RGB)")
      background = Image.new("RGB", img.size, (255, 255, 255))
      background.paste(img, mask=img.split()[3])
      background.save(filepath, 'PNG', quality=100)
      enhanced_filepath = EnhancedImageGenerator(filepath)
      return enhanced_filepath
    elif len(img.getbands()) == 3:
      print("Image has", len(img.getbands()), "channels (RGB)")
      enhanced_filepath = EnhancedImageGenerator(filepath)
      return enhanced_filepath
    return filepath  
  except Exception as e:
    print(f"Error enhancing image: {e}")
    return filepath  # Return original filepath on error

def YoloOcrProcessing(filepath, model, names, country):
    """
    Processes the image for object detection and text extraction.

    Args:
        filepath: Path to the image file.
        model: The YOLO model for object detection.
        names: List of class names for the YOLO model.

    Returns:
        A dictionary containing extracted text data or None if no objects found.
    """

    UAE_OMIT = ['uae_passport_front', 'uae_passport_photo', 'uae_passport_signature']
    INDIA_OMIT = ['indian_passport_front', 'indian_passport_photo', 'indian_passport_signature']
    
    UAE_REPLACE_STR = 'uae_passport_'
    INDIA_REPLACE_STR = 'indian_passport_'
    
    FINAL_OMIT = []
    FINAL_REPLACE_STR = ""
    
    if country == "uae":
        FINAL_OMIT = UAE_OMIT.copy()
        FINAL_REPLACE_STR = UAE_REPLACE_STR
    elif country == "in":
        FINAL_OMIT = INDIA_OMIT.copy()
        FINAL_REPLACE_STR = INDIA_REPLACE_STR
       
    results = model.predict(filepath, show=False)

    if results is None:
        return None  # Handle no detection case

    boxes = results[0].boxes.xyxy.cpu().tolist()
    clss = results[0].boxes.cls.cpu().tolist()
    image = cv2.imread(filepath)
    data = {}

    for box, cls in zip(boxes, clss):
        cls_name = names[int(cls)]
        if cls_name not in FINAL_OMIT:
            crop_obj = image[int(box[1]): int(box[3]), int(box[0]) : int(box[2])]
            result = pytesseract.image_to_string(crop_obj, config='--psm 6')  # Assuming scene text mode

            if result:
                data[cls_name.replace(FINAL_REPLACE_STR, "")] = result.replace('\n', '')

    return data
import easyocr
import cv2

def ExtractTextFromImage(image_path, confidence_threshold=0.5):
    reader = easyocr.Reader(['en'], gpu=False)
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text_data = reader.readtext(gray)

    accumulated_text = ""

    for bbox, text, confidence in text_data:
        accumulated_text = accumulated_text + " " + text

    print(accumulated_text)
    return accumulated_text

import io
import warnings
import numpy as np
from PIL import Image
import streamlit as st

# Suppress PyTorch/dynamic quantization UserWarnings in console
warnings.filterwarnings("ignore", category=UserWarning)

@st.cache_resource(show_spinner=False)
def get_ocr_reader():
    """
    Initializes and caches the EasyOCR Reader instance for English on CPU.
    Cached across reruns and sessions for optimal performance.
    """
    import easyocr
    return easyocr.Reader(["en"], gpu=False, verbose=False)

def extract_text_from_image(image_file_or_bytes) -> tuple[bool, str, str]:
    """
    Extracts readable text from an uploaded image using EasyOCR in memory.
    
    Args:
        image_file_or_bytes: A BytesIO object, file-like object, or raw bytes of the image.
        
    Returns:
        tuple (success: bool, text: str, message: str)
    """
    if not image_file_or_bytes:
        return False, "", "No image provided."
        
    try:
        # Load image into PIL and convert to RGB in memory
        if isinstance(image_file_or_bytes, bytes):
            image = Image.open(io.BytesIO(image_file_or_bytes)).convert("RGB")
        elif hasattr(image_file_or_bytes, "getvalue"):
            image = Image.open(io.BytesIO(image_file_or_bytes.getvalue())).convert("RGB")
        elif hasattr(image_file_or_bytes, "read"):
            image = Image.open(image_file_or_bytes).convert("RGB")
        else:
            image = Image.open(image_file_or_bytes).convert("RGB")
            
        img_np = np.array(image)
        reader = get_ocr_reader()
        
        # Run OCR with paragraph grouping
        results = reader.readtext(img_np, paragraph=True)
        
        # Fallback to standard line detection if paragraph returns empty
        if not results:
            results = reader.readtext(img_np, paragraph=False)
            
        extracted_lines = []
        for item in results:
            # EasyOCR returns (bbox, text) in paragraph mode or (bbox, text, prob) in standard mode
            text_str = item[1].strip() if len(item) > 1 else ""
            if text_str:
                extracted_lines.append(text_str)
                
        cleaned_text = "\n\n".join(extracted_lines).strip()
        
        if not cleaned_text or len(cleaned_text) < 5:
            return False, "", "No readable text detected in the uploaded image. Please ensure the screenshot is clear and in focus, or switch to Paste Job Text."
            
        word_count = len(cleaned_text.split())
        char_count = len(cleaned_text)
        return True, cleaned_text, f"Text extracted successfully ({word_count} words, {char_count} characters found)."
        
    except Exception as e:
        return False, "", f"Could not process image file: {str(e)}. Please upload a valid PNG, JPG, or JPEG file."

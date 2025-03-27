import streamlit as st
import cloudinary
import cloudinary.uploader
from groq import Groq
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO

# Cloudinary Configuration
cloudinary.config(
    cloud_name="dgojt5udn",  
    api_key="635178667269684",        
    api_secret="kBvCa2ROf5mMS4bTFeV4DGaeOos"    
)

# Initialize Groq client
client = Groq(api_key="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")

def resize_image(image, max_size=800):
    """Resize image while maintaining aspect ratio."""
    width, height = image.size
    if max(width, height) > max_size:
        scaling_factor = max_size / max(width, height)
        new_size = (int(width * scaling_factor), int(height * scaling_factor))
        return image.resize(new_size, Image.LANCZOS)
    return image

def upload_image(image):
    """Uploads a resized image to Cloudinary."""
    try:
        image = resize_image(image)  # Resize before upload
        img_bytes = BytesIO()
        image.save(img_bytes, format="PNG")  
        img_bytes.seek(0)
        response = cloudinary.uploader.upload(img_bytes)
        return response['secure_url']
    except Exception as e:
        st.error(f"⚠️ Error uploading image: {e}")
        return None

def extract_text_from_image(image_url):
    """Extracts specific details from a passport image using Groq API."""
    prompt_text = (
        "Extract the following details from this passport image:\n"
        "- FULL NAME\n"
        "- PASSPORT NUMBER\n"
        "- NATIONALITY\n"
        "- DATE OF BIRTH\n"
        "- DATE OF ISSUE\n"
        "- DATE OF EXPIRY\n"
        "- PLACE OF ISSUE\n"
        "- GENDER\n"
        "- ADDRESS\n\n"
        "If any of these details are missing, return 'NOT AVAILABLE'.\n"
        "Ensure all extracted text is in UPPERCASE."
    )

    response = client.chat.completions.create(
        model="llama-3.2-90b-vision-preview",
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]}
        ],
        temperature=0.2,
        max_completion_tokens=1024,
        top_p=1,
        stream=False
    )

    return response.choices[0].message.content.upper()


def convert_pdf_to_image(pdf_file):
    """Converts the first page of a PDF to an image using PyMuPDF (fitz)."""
    try:
        pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        first_page = pdf_document[0]
        pix = first_page.get_pixmap(dpi=200)  # Convert PDF to image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return img
    except Exception as e:
        st.error(f"⚠️ Error converting PDF: {e}")
        return None

def main():
    st.set_page_config(layout="wide")
    st.title("📸 Image & PDF Detail Extractor")
    
    uploaded_file = st.file_uploader("Upload an image or PDF", type=["png", "jpg", "jpeg", "pdf"])

    if uploaded_file:
        col1, col2 = st.columns([1, 1])  # Two equal columns
        
        if uploaded_file.type == "application/pdf":
            st.info("📄 PDF detected! Extracting the first page...")
            image = convert_pdf_to_image(uploaded_file)
            if image is None:
                return
        else:
            image = Image.open(uploaded_file)

        with col1:
            st.image(image, caption="📌 Processed Image", use_container_width=True)

        with st.status("Processing image... Please wait.", expanded=False) as status:
            image_url = upload_image(image)
            if image_url:
                with col1:
                    st.success("✅ Image uploaded successfully!")
                    st.image(image_url, caption="🌍 Hosted on Cloudinary", use_container_width=True)

                extracted_text = extract_text_from_image(image_url)

                with col2:
                    st.subheader("🔍 Extracted Details")
                    st.write(extracted_text)

                status.update(label="✅ Processing complete!", state="complete")

if __name__ == "__main__":
    main()

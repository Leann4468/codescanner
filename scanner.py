import streamlit as st
import cv2
import numpy as np
from PIL import Image
from pyzbar import pyzbar
import webbrowser
import winsound
from datetime import datetime
import os

# Function to open detected code in a browser
def open_code_in_browser(data, open_in):
    if open_in == "Google":
        webbrowser.open(f"https://www.google.com/search?q={data}")
    elif open_in == "Amazon":
        webbrowser.open(f"https://www.amazon.com/s?k={data}")

# Function to scan image for barcodes and QR codes
def scan_image_for_codes(image):
    return pyzbar.decode(image)

# Function to display a new page
def new_page():
    st.title("New Page")
    st.write("Welcome to the new page!")
    st.write("This is a new page.")

# Function to make a beep sound
def beep():
    winsound.Beep(2500, 500)

# Function to load YOLO model
def load_yolo_model():
    net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
    classes = []
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]
    layers_names = net.getLayerNames()
    
    # Check the structure of the output from net.getUnconnectedOutLayers()
    unconnected_out_layers = net.getUnconnectedOutLayers()
    if isinstance(unconnected_out_layers, np.ndarray):
        # For newer versions of OpenCV, it returns a flat list
        output_layers = [layers_names[i - 1] for i in unconnected_out_layers]
    else:
        # For older versions of OpenCV, it returns a list of lists
        output_layers = [layers_names[i[0] - 1] for i in unconnected_out_layers]
    
    return net, classes, output_layers


# Function to detect objects using YOLO
def detect_objects(img, net, output_layers):
    height, width, channels = img.shape
    blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)
    class_ids, confidences, boxes = [], [], []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)
    return boxes, confidences, class_ids

# Main page function
def main_page():
    st.sidebar.title("Sidebar")
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4481/4481064.png", use_column_width=True)
    option = st.sidebar.selectbox("Select an option", [" ", "Upload Image", "Barcode", "QR Code", "Next"])

    st.markdown(
        """
        <style>
        .stApp {
            background: url("https://img.freepik.com/free-photo/artistic-blurry-colorful-wallpaper-background_58702-8628.jpg?size=626&ext=jpg") no-repeat center fixed;
            background-size: cover;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if option == "Upload Image":
        st.title("Upload Image")
        st.write("Upload an image to scan for barcodes or QR codes.")
        open_in = st.radio("Open detected code in:", ["Google", "Amazon"])
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            image_np = np.array(image)
            st.image(image, caption='Uploaded Image.', use_column_width=True)
            st.write("")
            st.write("Scanning for barcodes and QR codes...")
            decoded_objects = scan_image_for_codes(image_np)
            for obj in decoded_objects:
                st.write(f"Detected {obj.type}: {obj.data.decode('utf-8')}")
                open_code_in_browser(obj.data.decode('utf-8'), open_in)

    elif option == "Barcode":
        st.title("Barcode Page")
        st.write("Welcome to the barcode page!")
        open_in = st.radio("Open detected code in:", ["Google", "Amazon"])
        display_datetime = st.checkbox("Display detection date and time")
        st.write("Open the camera to scan barcodes.")
        if st.button("Start Barcode Scanner"):
            st.session_state.camera_active = True
            run_camera("barcode", open_in, display_datetime)

    elif option == "QR Code":
        st.title("QR Code Page")
        open_in = st.radio("Open detected code in:", ["Google", "Amazon"])
        display_datetime = st.checkbox("Display detection date and time")
        st.write("Welcome to the QR code page!")
        st.write("Open the camera to scan QR codes.")
        if st.button("Start QR Code Scanner"):
            st.session_state.camera_active = True
            run_camera("qrcode", open_in, display_datetime)

    elif option == "Next":
        new_page()

# Function to run the camera
def run_camera(code_type, open_in, display_datetime):
    cap = cv2.VideoCapture(0)
    stop_button = st.button("Stop Scanner")
    net, classes, output_layers = load_yolo_model()
    
    while st.session_state.camera_active:
        ret, frame = cap.read()
        if not ret:
            st.write("Failed to capture image")
            break
        
        boxes, confidences, class_ids = detect_objects(frame, net, output_layers)
        for box in boxes:
            x, y, w, h = box
            roi = frame[y:y+h, x:x+w]
            
            # Check if the ROI has valid dimensions
            if roi.size == 0 or roi.shape[0] == 0 or roi.shape[1] == 0:
                continue
            
            # Convert ROI to grayscale for faster barcode/QR code detection
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            decoded_objects = scan_image_for_codes(gray_roi)
            if decoded_objects:  # Check if any objects were detected
                for obj in decoded_objects:
                    detected_code = obj.data.decode('utf-8')
                    st.write(f"{code_type.capitalize()} detected: {detected_code}")
                    if display_datetime:
                        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.write(f"Detected at: {current_datetime}")
                    beep()
                    open_code_in_browser(detected_code, open_in)
                    st.session_state.camera_active = False
                    break
        
        if stop_button:
            st.session_state.camera_active = False
            break
    
    cap.release()


if __name__ == "__main__":
    if 'camera_active' not in st.session_state:
        st.session_state.camera_active = False
    main_page()

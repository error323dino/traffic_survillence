import cv2
import pandas as pd
from ultralytics import YOLO
from tracker import *
import json
import zmq
import logging
import atexit
import subprocess

# Set logging level to WARNING to suppress debug and info messages
logging.getLogger("ultralytics").setLevel(logging.WARNING)
context = zmq.Context()

# Create a subscriber socket to receive messages from the traffic light controller
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://localhost:5555")
subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

# Create a publisher socket to send messages to the processes
publisher = context.socket(zmq.PUB)
publisher.bind("tcp://*:5554")  

# Create a publisher socket to send messages to the processes
ach = context.socket(zmq.PUB)
ach.bind("tcp://*:5553")  

process = subprocess.Popen(["python", "red2.py"])

def get_process_id(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
        return config.get("process_id", "Unknown Process")

# Function to handle mouse events (for debugging)
def RGB(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        colorsBGR = [x, y]


# Define the video input paths and names
video_inputs = {
    'Camera2': cv2.VideoCapture('veh2.mp4'),
}

# Load the YOLO model
model = YOLO('yolov8s.pt')
# Load the COCO class list
with open("coco.txt", "r") as my_file:
    data = my_file.read()
    class_list = data.split("\n")

count = 0

# Initialize variables for tracking and traffic light behavior
tracker = Tracker()
cy1, cy2, cy3 = 322, 368, 272 
offset = 6
vh_down = {}
vh_up = {}
vh_down_right = {}
list_down_red = []
counter_in = []


traffic_light_state = 'red'
initial_traffic_light_duration = 100  # Initial green light duration
traffic_light_duration = initial_traffic_light_duration # Current green light duration starts from the initial value
max_duration = 200  # Maximum allowed green light duration
min_duration = 50   # Minimum allowed green light duration
car_count_threshold = 5  # Adjust this threshold as per your requirements

# Initialize traffic light information for each video input
traffic_lights = {video_name: {'state': 'red', 'timer': 0, 'duration': initial_traffic_light_duration} for video_name in video_inputs}

# Create windows for each video input
for video_name in video_inputs:
    cv2.namedWindow(f'Camera {video_name}')
    cv2.setMouseCallback(f'Camera {video_name}', RGB) 
intent_received = False

subscriber.setsockopt(zmq.RCVTIMEO, 0)

while True:
    for video_name, video_path in video_inputs.items():
        ret, frame = video_path.read()
    if not ret:
        break

    count += 1
    if count % 15 != 0:
        continue
    frame = cv2.resize(frame, (960, 500))

    while True:
        try:
                intent_message = subscriber.recv_string()
                print("Received intent message:", intent_message)
                if "Changing to Green for Process 2" in intent_message:
                    print("Received intent to change to Green. Starting green light process.")
                    
                    intent_received = True 
                    acknowledgment = "Intent received and processed"
    
                    ach.send_string(acknowledgment)

                    print("Sent acknowledgment:", acknowledgment)

        except zmq.error.Again:
            break

    if intent_received :
        try:
            print("CAM2 GREEN LO")
            traffic_light_state = 'green'
            if process is not None:
                process.terminate()
            list_down_red = []
        except zmq.error.Again:
            pass
    
    print(traffic_light_duration)
    # Update Traffic Light State
    if traffic_light_duration == 0:
        traffic_light_state = 'red'
        messageBack = "Red"
        # Send the message
        print("CAM2 RED LO")
        process = subprocess.Popen(["python", "red2.py"])
        publisher.send_string(messageBack)
        atexit.register(publisher.close)
        intent_received = False
        traffic_light_duration = initial_traffic_light_duration  # Reset to initial value
        
    if traffic_light_state == 'green':
           traffic_light_duration -= 1
   
    # Draw Traffic Light
    traffic_light_color = (0, 0, 255) if traffic_light_state == 'red' else (0, 255, 0)
    cv2.circle(frame, (50, 50), 20, traffic_light_color, -1)

    results = model.predict(frame)
    a = results[0].boxes.boxes
    px = pd.DataFrame(a).astype("float")

    for index, row in px.iterrows():
        x1 = int(row[0])
        y1 = int(row[1])
        x2 = int(row[2])
        y2 = int(row[3])
        d = int(row[5])
        c = class_list[d]
        if 'car' in c:
       
                 # Check if car is going down at cy3 during red light
            if traffic_light_state == 'red' and cy3 < (y1 + offset) and cy3 > (y1 - offset):
                traffic_light_duration += 5
                # Only append if the car hasn't already been counted
                if [x1, y1, x2, y2] not in list_down_red:
                    list_down_red.append([x1, y1, x2, y2])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Draw in red


            # Add object label
            label = class_list[d]
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            
            # Draw lines
        line_color = (255, 255, 255)


        cv2.line(frame, (0, cy3), (frame.shape[1], cy3), line_color, 1)
        cv2.putText(frame, '3rd line', (0, cy3 - 5), cv2.FONT_HERSHEY_COMPLEX, 0.8, line_color, 2)



        # Display car count for going down-right at cy3 during the red light
        c_down_right = len(list_down_red)
        cv2.putText(frame, ('Cars Stop:') + str(c_down_right), (60, 80), cv2.FONT_HERSHEY_COMPLEX, 0.8, (255, 0, 0), 2)


        # Display the video window for this video input
        cv2.imshow(f"Camera {video_name}", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

# Release video captures and close windows
for video_path in video_inputs.values():
    video_path.release()
cv2.destroyAllWindows()


if __name__ == "__main__":
    process_id = get_process_id("process2.json")  # Use the appropriate config file for each process


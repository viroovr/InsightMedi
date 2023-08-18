import cv2 # Computer vision library
from random import randint # Handles the creation of random integers
 
# Make sure the video file is in the same directory as your code
file_prefix = 'street'
filename = file_prefix + '.mp4'
file_size = (1920,1080) # Assumes 1920x1080 mp4
 
# We want to save the output to a video file
output_filename = file_prefix + '_object_tracking.mp4'
output_frames_per_second = 20.0
 
# OpenCV has a bunch of object tracking algorithms. We list them here.
type_of_trackers = ['BOOSTING', 'MIL', 'KCF','TLD', 'MEDIANFLOW', 'GOTURN', 
                     'MOSSE', 'CSRT']
 
# CSRT is accurate but slow. You can try others and see what results you get.            
desired_tracker = 'CSRT'
 
# Generate a MultiTracker object    
multi_tracker = cv2.legacy.MultiTracker_create()
 
# Set bounding box drawing parameters
from_center = False # Draw bounding box from upper left
show_cross_hair = False # Don't show the cross hair
                                          
def generate_tracker(type_of_tracker):
  """
  Create object tracker.
     
  :param type_of_tracker string: OpenCV tracking algorithm 
  """
  if type_of_tracker == type_of_trackers[0]:
    tracker = cv2.TrackerBoosting_create()
  elif type_of_tracker == type_of_trackers[1]:
    tracker = cv2.TrackerMIL_create()
  elif type_of_tracker == type_of_trackers[2]:
    tracker = cv2.TrackerKCF_create()
  elif type_of_tracker == type_of_trackers[3]:
    tracker = cv2.TrackerTLD_create()
  elif type_of_tracker == type_of_trackers[4]:
    tracker = cv2.TrackerMedianFlow_create()
  elif type_of_tracker == type_of_trackers[5]:
    tracker = cv2.TrackerGOTURN_create()
  elif type_of_tracker == type_of_trackers[6]:
    tracker = cv2.TrackerMOSSE_create()
  elif type_of_tracker == type_of_trackers[7]:
    tracker = cv2.TrackerCSRT_create()
  else:
    tracker = None
    print('The name of the tracker is incorrect')
    print('Here are the possible trackers:')
    for track_type in type_of_trackers:
      print(track_type)
  return tracker
 
def main():
 
  # Load a video
  cap = cv2.VideoCapture(filename)
 
  # Create a VideoWriter object so we can save the video output
  fourcc = cv2.VideoWriter_fourcc(*'mp4v')
  result = cv2.VideoWriter(output_filename,  
                           fourcc, 
                           output_frames_per_second, 
                           file_size) 
 
  # Capture the first video frame
  success, frame = cap.read() 
 
  bounding_box_list = []
  color_list = []   
 
  # Do we have a video frame? If true, proceed.
  if success:
 
    while True:
     
          # Draw a bounding box over all the objects that you want to track_type
      # Press ENTER or SPACE after you've drawn the bounding box
      bounding_box = cv2.selectROI('Multi-Object Tracker', frame, from_center, 
        show_cross_hair) 
 
      # Add a bounding box
      bounding_box_list.append(bounding_box)
             
      # Add a random color_list
      blue = 255 # randint(127, 255)
      green = 0 # randint(127, 255)
      red = 255 #randint(127, 255)
      color_list.append((blue, green, red))
 
      # Press 'q' (make sure you click on the video frame so that it is the
      # active window) to start object tracking. You can press another key
      # if you want to draw another bounding box.           
      print("\nPress q to begin tracking objects or press " +
        "another key to draw the next bounding box\n")
 
      # Wait for keypress
      k = cv2.waitKey() & 0xFF
 
      # Start tracking objects if 'q' is pressed            
      if k == ord('q'):
        break
 
    cv2.destroyAllWindows()
         
    print("\nTracking objects. Please wait...")
         
    # Set the tracker
    type_of_tracker = desired_tracker   
             
    for bbox in bounding_box_list:
         
      # Add tracker to the multi-object tracker
      multi_tracker.add(generate_tracker(type_of_tracker), frame, bbox)
       
    # Process the video
    while cap.isOpened():
         
      # Capture one frame at a time
      success, frame = cap.read() 
         
      # Do we have a video frame? If true, proceed.
      if success:
 
        # Update the location of the bounding boxes
        success, bboxes = multi_tracker.update(frame)
 
        # Draw the bounding boxes on the video frame
        for i, bbox in enumerate(bboxes):
          point_1 = (int(bbox[0]), int(bbox[1]))
          point_2 = (int(bbox[0] + bbox[2]), 
            int(bbox[1] + bbox[3]))
          cv2.rectangle(frame, point_1, point_2, color_list[i], 5)
                 
        # Write the frame to the output video file
        result.write(frame)
 
      # No more video frames left
      else:
        break
         
  # Stop when the video is finished
  cap.release()
     
  # Release the video recording
  result.release()
 
main()
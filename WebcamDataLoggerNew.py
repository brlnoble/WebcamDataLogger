#This program was made to act as a stand in data logger when the device died
#It takes in a charge number, and duration and takes a photo with a webcam every 30 minutes
#The webcam should be pointed at the digital readout of the temperature on the furnace
#Photos are saved in a folder according to the charge number

#---Brandon Noble, January 2022---


import cv2
from time import time
import datetime
import os
import sys
import PySimpleGUI as sg

#setup camera
cam = cv2.VideoCapture(0, cv2.CAP_DSHOW) #SECOND PART REQUIRED OR IT DOESNT WORK IN WINDOWS 7
cam.set(3,1920) #sets resolution to 1080p since default is 1080p
cam.set(4,1080)


#-----GUI WINDOW AND INPUT-----
sg.theme('DefaultNoMoreNagging')
font = ("Arial, 16")
titleFont = ("Arial, 20")
sg.theme_text_element_background_color('#EEE')
sg.theme_text_color('#333')
sg.theme_background_color('#EEE')

layout = [  [sg.Text('Enter the charge number, and duration before hitting submit.', font=titleFont)],
            [sg.Text('Charge Number:',size=(15,1), font=font), sg.Input(key='-C-', enable_events=True,size=(15,1), font=font)],
            [sg.Text('Number of Hours:',size=(15,1), font=font), sg.Input(key='-H-', enable_events=True,size=(15,1), font=font)],
            [sg.Image(filename='', key='image')],
            [sg.Button('Submit',size=(10,2), font=font), sg.Push(), sg.Button('Exit',size=(10,2), font=font, button_color='Red')]  ]


window = sg.Window('Webcame Data Logger', layout, no_titlebar = True, keep_on_top=True, location=(600, 200), element_justification='c')
duration = 0

while True:
    event, values = window.read(timeout=100)
    if event == 'Exit': #CLOSE PROGRAM
        window.close()
        sys.exit()
        break
    
    #Allow only numbers, max 5 characters for charge
    if event == '-C-' and values['-C-'] and values['-C-'][-1] not in ('0123456789') or len(values['-C-']) > 5:
        window['-C-'].update(values['-C-'][:-1])
    if event == '-H-' and values['-H-'] and values['-H-'][-1] not in ('0123456789'):
        window['-H-'].update(values['-H-'][:-1])
    if event == 'Submit':
        chargeNum = values['-C-']
        duration = values['-H-']
        
        #validate input
        if len(chargeNum) != 5:
            sg.Popup('Please enter a 5 digit charge number', keep_on_top=True)
            continue
        elif len(duration) == 0:
            sg.popup('Please enter the number of hours', keep_on_top=True)
            continue
        else:
            break
    #Display webcam current view
    ret, frame = cam.read()
    if not ret:
        print("failed to grab frame")
        sg.popup('Could not find camera!')
        sys.exit()
    frame = cv2.resize(frame, (640,360), interpolation =cv2.INTER_AREA) #make view slightly smaller
    imgbytes = cv2.imencode('.png', frame)[1].tobytes()  # ditto
    window['image'].update(data=imgbytes)
    
window.close()
cv2.destroyAllWindows()


#-----SETUP VARIABLES-----
interval = 1800 #number of seconds between images - currently 30 minutes
multiplier = 3600/interval #multiply the duration to account for taking pictures more frequently than every hour
img_counter = 0 #used to keep photos in numerical order
duration = int(duration)+1 #extra hour
currTime = float(time())
prevTime = currTime
startTime = datetime.datetime.fromtimestamp(currTime)



#-----PATH-----
if getattr(sys, 'frozen', False): #If an executable, it needs to use this or it takes the temp folder as current path
    path = os.path.dirname(sys.executable)
elif __file__: #if running as a python script
    path = os.path.dirname(__file__)
    
path = path + '/Photos/' + chargeNum #new folder to be created
print(path)

#Check if path exists, if not continue and create path
if os.path.isdir(path) == True:
    sg.popup('Charge number {} already exists! Please try again.'.format(chargeNum), keep_on_top=True)
    sys.exit() #EXIT PROGRAM
else:
    os.mkdir(path)
path = path + '/' #make sure path is a folder


#-----INITAL PHOTO-----
ret, frame = cam.read()
if not ret:
    print("failed to grab frame")
    sg.popup('Could not find camera!') #Failed to capture image
    sys.exit()

img_name = "{}Charge_{}_{}.png".format(path,chargeNum,img_counter)
cv2.imwrite(img_name, frame)
print("Photo {}".format(img_counter))
prevTime = currTime



#-----NEW WINDOW TO SHOW PROGRESS-----
layout = [  [sg.Text('---STATUS---', font=titleFont)],
            [sg.Text()],
            [sg.Text('Charge:', font=font), sg.Push(), sg.Text(chargeNum,font=font)],
            [sg.Text('Duration:', font=font), sg.Push(), sg.Text(str(duration) + ' hours', font=font)],
            [sg.Text('Started:', font=font),sg.Push(), sg.Text(startTime.strftime("%d/%m/%y - %H:%M"), font=font)],
            [sg.ProgressBar(1, orientation='h', size=(30,20),key='-P-')],
            [sg.Button('CANCEL', font=font, button_color='Red')] ]

window = sg.Window('Recording Data', layout, no_titlebar = True, keep_on_top=True, element_justification='c')

event, values = window.Read(timeout=0)
window['-P-'].UpdateBar(1, duration*multiplier+1) #Update progress bar

while(img_counter < duration*multiplier):
    #check to see if the cancel button was clicked and exit loop if clicked
    event, values = window.Read(timeout=0)
    if event == 'CANCEL' or event == None:
        window.close()
        sg.popup('Logging cancelled')
        break
    
    
    currTime = float(time()) #current time
    if currTime >= (prevTime + interval): #if next image should be taken
        #update bar with loop value +1 so that bar eventually reaches the maximum
        img_counter += 1
        window['-P-'].UpdateBar(img_counter+1, duration*multiplier+1) #update progress bar
        prevTime = currTime
        
        #TAKE PHOTO
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame")
            sg.popup('Could not find camera!') #Failed to capture image
            sys.exit()
        img_name = "{}Charge_{}_{}.png".format(path,chargeNum,img_counter)
        cv2.imwrite(img_name, frame)
        print("Photo {}".format(img_counter))


#-----END PROGRAM-----
window.close()
cam.release()

# sg.popup('Logging Finished', keep_on_top=True) #Informs user the logging was completed
    
#-----COMPILE-----
#make sure file is in Desktop/Code
#open CMD and type the following:
#cd Desktop/Code
#pyinstaller -wF FILENAME.py
#
#exe found in dist folder

#-----REFERENCES-----
# https://www.codegrepper.com/code-examples/python/cap+%3D+cv2.videocapture%280%29
# https://stackoverflow.com/questions/5458048/how-can-i-make-a-python-script-standalone-executable-to-run-without-any-dependen
# https://answers.opencv.org/question/234933/opencv-440modulesvideoiosrccap_msmfcpp-682-cvcapture_msmfinitstream-failed-to-set-mediatype-stream-0-640x480-30-mfvideoformat_rgb24unsupported-media/
# https://stackoverflow.com/questions/3430372/how-do-i-get-the-full-path-of-the-current-files-directory
# https://pysimplegui.readthedocs.io/en/latest/cookbook/
# https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_OpenCV_Webcam.py
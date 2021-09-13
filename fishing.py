from global_hotkeys import *
import time
import os
import numpy as np
import cv2 as cv
import pyautogui #Really useful for this tool. Go back to this documentation for new features
import win32api
import win32con

image_window = "Source Image"
result_window = "Result window"

#States
#Unknown
#Waiting
#Casted
#Reeling
#Slacking
#Success

templatePathDictionary = { #Need template for camera turned
    "casted": "./TestData/templates/bobber_cropped.png",
    "hook": "./TestData/templates/hook_cropped.png",
    "success": "./TestData/templates/success_cropped.png",
    #"casting": "./TestData/templates/casting_cropped.png",
    "waiting": "./TestData/templates/waiting_cropped_alt.png",
    #"lantern": "./TestData/templates/lantern_cropped.png",

    "green1": "./TestData/templates/green1_cropped.png",
    "green2": "./TestData/templates/green2_cropped.png",
    "green3": "./TestData/templates/green3_cropped.png",
    "green4": "./TestData/templates/green4_cropped.png",

    "orange1": "./TestData/templates/orange1_cropped.png",
    "orange2": "./TestData/templates/orange2_cropped.png",
    "orange3": "./TestData/templates/orange3_cropped.png",

    "red1": "./TestData/templates/red1_cropped.png",
    "red2": "./TestData/templates/red2_cropped.png"
}

paused = True
keepRunning = True
imageAtLastCast = None
slackThreshold = 30
slackCounter = 0
fishCounter = 0

def main():
    global imageAtLastCast
    global fishCounter
    global slackCounter

    # Register all of our keybindings
    register_hotkeys(bindings)

    # Finally, start listening for keypresses
    start_checking_hotkeys()
    templates = readTemplates()
    currentState = "Unknown"
    currentAction = "Wait"
    print("Press Pause when ready to begin...")
    while keepRunning :
        if paused == True:
            time.sleep(0.25)
            continue

        print("********************************************")
        startTime = time.time()
        currentImage = takeScreenshot()
        highestConfidence = -1
        newState = ""
        
        if imageAtLastCast is None:
            imageAtLastCast = currentImage

        #print("CurrentState: ",currentState)
        for key, value in templates.items():
            matchConfidence, markedImage = compareImages(currentImage, value)
            #print("Current Match: ",key," Value: ",matchConfidence)
            #cv.imwrite("test_"+key+"matchedImage.png", markedImage)
            if matchConfidence > highestConfidence:
                highestConfidence = matchConfidence
                newState = key
        print("NewState: ",newState)

        action = determineAction(currentState, newState)
        moveConfidence = 0
        if action == "Cast":
            moveConfidence, _markedImage = compareImages(currentImage, imageAtLastCast)
            print("MoveConfidence: ", moveConfidence)
            if moveConfidence < 0.89: #If confidence is low that means camera turned, so turn us back before casting
                action = "TurnCast"
        
        print("PerformAction: ",action)
        performAction(currentAction, action)

        if action == "Cast" or action == "TurnCast":
            imageAtLastCast = currentImage
        currentAction = action
        currentState = newState

        endTime = time.time()
        print("Step Duration: ",endTime-startTime)
    
    print("Stopping")
    print("Caught "+fishCounter+ " Fish")
        
def compareImages(image, template):
    confidenceValue = 0
    match_method = 3 #Like 4
    w, h = template.shape[:-1]
    result = cv.matchTemplate(image, template, match_method)
    #cv.normalize( result, result, 0, 1, cv.NORM_MINMAX, -1 )
    minVal, maxVal, minLoc, maxLoc = cv.minMaxLoc(result, None)
    ## [match_loc]
    if (match_method == cv.TM_SQDIFF or match_method == cv.TM_SQDIFF_NORMED):
        matchLoc = minLoc
        confidenceValue = minVal
    else:
        matchLoc = maxLoc
        confidenceValue = maxVal
    ## [match_loc]
    img_display = image.copy()
    cv.rectangle(img_display, matchLoc, (matchLoc[0] + template.shape[0], matchLoc[1] + template.shape[1]), (0,0,0), 2, 8, 0 )

    return confidenceValue, img_display

def readTemplates():
    #filedata = {key: open(value, 'r') for key, value in templateDictionary.items()}

    templateDictionary = {}
    for key, value in templatePathDictionary.items():
        templateImage = scaleImage(cv.imread(value, cv.IMREAD_COLOR))
        #cv.imwrite(key+"template.png", templateImage)
        templateDictionary[key] = templateImage

    return templateDictionary

def takeScreenshot():
    # take screenshot using pyautogui
    image = pyautogui.screenshot(region=(1400,300,1000,1500))
    #image = pyautogui.screenshot(region=(0,0, 300, 400))
    
    # since the pyautogui takes as a 
    # PIL(pillow) and in RGB we need to 
    # convert it to numpy array and BGR 
    # so we can write it to the disk
    image = cv.cvtColor(np.array(image),
                        cv.COLOR_BGR2RGB)
    
    # writing it to the disk using opencv
    #cv.imwrite("testImage.png", image)
    return scaleImage(image)

def scaleImage(image):
    scale_percent = 20 # percent of original size
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
    
    # resize image
    resized = cv.resize(image, dim, interpolation = cv.INTER_AREA)
    return resized

def performAction(previousAction, newAction):
    global fishCounter
    global slackThreshold
    global slackCounter

    if(newAction == "Wait"):
        return #Do Nothing
    
    if(newAction == "Hook"):
        if(previousAction == "Hook"):
            print("Skipping hook")
            return #Do Nothing because we clicked last time
        else:
            pyautogui.click()
            time.sleep(1)

    if(newAction == "Caught"):
        print("Caught Fish!")
        fishCounter += 1
        time.sleep(7)
    
    if(newAction == "Cast"):
        #Click and Hold and release after specified time
        #pyautogui.keyDown("altleft")
        pyautogui.mouseDown()
        time.sleep(1.9)
        pyautogui.mouseUp()
        time.sleep(2)

    if(newAction == "Reel"):
        #Click and Hold
        pyautogui.mouseDown()

    if(newAction == "Slack"):
        #Release Click
        slackCounter += 1
        if(slackCounter > slackThreshold):
            print("TOO MUCH SLACK, FORCING REEL")
            pyautogui.mouseDown()
        else:
            pyautogui.mouseUp()
    else:
        slackCounter = 0

    if(newAction == "TurnCast"):
        moveCamera()
        time.sleep(2)
        togglePauseHotkey()

def determineAction(previousState, newState):
    action = "Unknown"
    if(newState == "lantern"):
        action = "Turn"
    elif(previousState == "Unknown"):
        action = getActionForUnknownState(newState)
    elif(previousState == "casted"):
        action = getActionForCastedState(newState)
    elif(previousState == "hook"):
        action = getActionForHookState(newState)
    elif(previousState == "success"):
        action = getActionForSuccessState(newState)
    elif(previousState == "casting"):
        action = "Wait" #getActionForCastingState(newState)
    elif(previousState == "waiting"):
        action = getActionForWaitingState(newState)
    elif(previousState == "green1" or previousState == "green2" or previousState == "green3" or previousState == "green4"):
        action = getActionForGreenState(newState)
    elif(previousState == "orange1" or previousState == "orange2" or previousState == "orange3"):
        action = getActionForOrangeState(newState)
    elif(previousState == "red1" or previousState == "red2"):
        action = getActionForRedState(newState)
    return action

def getActionForUnknownState(state):   
    if(state == "Unknown" or state == "Error"):
        return "Wait" #Not a clue
    if(state == "casted"):
        return "Wait"
    if(state == "hook"):
        return "Hook"
    if(state == "success"):
        return "Wait"
    if(state == "casting"):
        return "Wait"
    if(state == "waiting"):
        return "Cast"
    if(state == "green1" or state == "green2" or state == "green3" or state == "green4"):
        return "Reel"
    if(state == "orange1" or state == "orange2" or state == "orange3"):
        return "Slack"
    if(state == "red1" or state == "red2"):
        return "Slack"

def getActionForCastedState(state):
    if(state == "Unknown"):
        return "Wait"
    if(state == "casted"):
        return "Wait"
    if(state == "hook"):
        return "Wait"
    if(state == "success"):
        return "Wait"
    if(state == "casting"):
        return "Error"
    if(state == "waiting"):
        return "Cast"
    if(state == "green1" or state == "green2" or state == "green3" or state == "green4"):
        return "Reel"
    if(state == "orange1" or state == "orange2" or state == "orange3"):
        return "Reel"
    if(state == "red1" or state == "red2"):
        return "Slack"

def getActionForHookState(state):
    if(state == "Unknown"):
        return "Wait"
    if(state == "casted"):
        return "Wait"
    if(state == "hook"):
        return "Hook"
    if(state == "success"):
        return "Wait"
    if(state == "casting"):
        return "Error"
    if(state == "waiting"):
        return "Error"
    if(state == "green1" or state == "green2" or state == "green3" or state == "green4"):
        return "Reel"
    if(state == "orange1" or state == "orange2" or state == "orange3"):
        return "Reel"
    if(state == "red1" or state == "red2"):
        return "Slack"

def getActionForSuccessState(state):
    if(state == "Unknown"):
        return "Wait"
    if(state == "casted"):
        return "Wait"
    if(state == "hook"):
        return "Wait"
    if(state == "success"):
        return "Wait"
    if(state == "casting"):
        return "Wait"
    if(state == "waiting"):
        return "Cast"
    if(state == "green1" or state == "green2" or state == "green3" or state == "green4"):
        return "Reel"
    if(state == "orange1" or state == "orange2" or state == "orange3"):
        return "Reel"
    if(state == "red1" or state == "red2"):
        return "Slack"

def getActionForWaitingState(state):
    if(state == "Unknown"):
        return "Wait"
    if(state == "casted"):
        return "Wait"
    if(state == "hook"):
        return "Wait"
    if(state == "success"):
        return "Wait"
    if(state == "casting"):
        return "Wait"
    if(state == "waiting"):
        return "Cast"
    if(state == "green1" or state == "green2" or state == "green3" or state == "green4"):
        return "Reel"
    if(state == "orange1" or state == "orange2" or state == "orange3"):
        return "Reel"
    if(state == "red1" or state == "red2"):
        return "Slack"
        
def getActionForGreenState(state):
    if(state == "Unknown"):
        return "Wait"
    if(state == "casted"):
        return "Error"
    if(state == "hook"):
        return "Caught"
    if(state == "success"):
        return "Wait"
    if(state == "casting"):
        return "Error"
    if(state == "waiting"):
        return "Cast"
    if(state == "green1" or state == "green2" or state == "green3" or state == "green4"):
        return "Reel"
    if(state == "orange1" or state == "orange2" or state == "orange3"):
        return "Reel"
    if(state == "red1" or state == "red2"):
        return "Slack"

def getActionForOrangeState(state):
    if(state == "Unknown"):
        return "Wait"
    if(state == "casted"):
        return "Error"
    if(state == "hook"):
        return "Caught"
    if(state == "success"):
        return "Wait"
    if(state == "casting"):
        return "Error"
    if(state == "waiting"):
        return "Cast"
    if(state == "green1" or state == "green2" or state == "green3" or state == "green4"):
        return "Reel"
    if(state == "orange1" or state == "orange2" or state == "orange3"):
        return "Reel"
    if(state == "red1" or state == "red2"):
        return "Slack"

def getActionForRedState(state):
    if(state == "Unknown"):
        return "Wait"
    if(state == "casted"):
        return "Error"
    if(state == "hook"):
        return "Caught"
    if(state == "success"):
        return "Wait"
    if(state == "casting"):
        return "Error"
    if(state == "waiting"):
        return "Cast"
    if(state == "green1" or state == "green2" or state == "green3" or state == "green4"):
        return "Reel"
    if(state == "orange1" or state == "orange2" or state == "orange3"):
        return "Slack"
    if(state == "red1" or state == "red2"):
        return "Slack"

def togglePauseHotkey():
    global paused
    global imageAtLastCast
    if paused == True:
        imageAtLastCast = takeScreenshot()
        paused = False
        print("Unpasued")
    else:
        paused = True
        print("Paused")

def stopApplication():
    print("Killing application")
    global keepRunning
    keepRunning = False

def moveCamera():
    print("Turning Camera")
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(1500), int(-800), 0, 0)

bindings = [
    [["pause"], None, togglePauseHotkey],
    [["end"], None, stopApplication],
    [["page_up"], None, moveCamera],
]

if __name__ == "__main__":
    main()
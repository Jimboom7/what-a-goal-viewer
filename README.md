# What A Goal Viewer

## About The Project

The WAG-Viewer is a simple python script that displays the current score for a **Pokemon Unite** game. Scores are collected by optical character recognition (OCR) on video input (screen or capture card).  
![Screenshot](https://i.imgur.com/ZnCUO34.png)  

## How to use

* Download the latest version from the [release page](https://github.com/Jimboom7/what-a-goal-viewer/releases) and unzip it (Windows only).
* Start the wag-viewer.exe.
* Select your source:
	* Monitor: Your primary monitor. Must be 16:9 format and displaying the game in fullscreen (Twitch or Youtube work too).
	* Virtualcam: Connect your capture card to your computer, set it up in OBS (preferably 1920x1080 output) and use the plugin [Virtualcam](https://obsproject.com/forum/resources/obs-virtualcam.949/) to provide DirectShow Output as a virtual webcam. Select the virtual webcam device number in the wag-viewer.
* Press the Start Button when the game starts.

## Development Setup

If you want to get the source running follow these steps:
- Install the dependencies with: `pip install requirements.txt`
- Download and Install Tesseract >= 5.0. Windows Installer can be found at [digi.bib.uni-mannheim.de/tesseract](https://digi.bib.uni-mannheim.de/tesseract/). Place the installation in the same folder as this project or adjust the path in the main.py that points to tesseract.  
- For better results download finetuned digits.traineddata from [here](https://github.com/Shreeshrii/tessdata_shreetest) and place it in the tesseract tessdata folder.


## How it works

The program checks the screen multiple times per second. Let's take this screenshot for example:  
![Original](https://i.imgur.com/1tLopkf.png)  
The marked areas are preprocessed in the following way:  
- Cut out the area
- Add a border (Tesseract doesn't like text at the edges of the image)
- Convert to HSV color space
- Apply a thresholding operation on yellow to get the text
- Remove artifacts by checking for non-viable contours (too large, weird forms, far from each other etc)
- Remove noise with erosion/dilation

In the example the final result for the left scoring area looks like this:  
![After Preprocessing](https://i.imgur.com/Mx3XfBx.png)  
This image is then given to tesseract for analysis and only a result with a strong confidence is accepted.  
The same applies to the right scoring area. For the score of the actual player the balls at the bottom of the screen are checked, because your own score notification is in the center of the screen and often hidden. When the balls suddenly drop to zero and the player is not dead (greyscreen) the score is accepted.

## Tests

The project contains a bunch of screenshots from the game. Running test.py will check all these screenshots for the correct scores and how confident they were detected. This can be used to evaluate the OCR and it's preprocessing.  
The program can be started with a "DEBUG" parameter to show additional logging and save the preprocessed images to the DEBUG dir.

## Known Problems
- Not all scores are detected correctly, some errors happen. In testing this was the case in 20% of the games.  
- End of game is not detected yet, you need to press Reset/Start after every game.  
- The program will not work when started in the middle of a game. The first goal of the game ("First Goal! +X") needs to be detected by the program, only after that happened it will start to look for normal scores.

## Possible improvements
- Train a tesseract model for the ingame font
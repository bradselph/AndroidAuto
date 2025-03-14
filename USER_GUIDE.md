# Android Automation Tool - User Guide

This guide will help you get started with the Android Automation Tool and explain its main features and capabilities.

## Table of Contents

- [Setup and Connection](#setup-and-connection)
- [Interface Overview](#interface-overview)
- [Recording Actions](#recording-actions)
- [Playing Back Actions](#playing-back-actions)
- [Working with Templates](#working-with-templates)
- [Creating Conditional Actions](#creating-conditional-actions)
- [Scheduling Tasks](#scheduling-tasks)
- [Settings and Configuration](#settings-and-configuration)
- [Troubleshooting](#troubleshooting)

## Setup and Connection

### Preparing Your Android Device

1. Enable Developer Options:
   - Go to Settings > About Phone
   - Tap "Build Number" 7 times until you see "You are now a developer"

2. Enable USB Debugging:
   - Go to Settings > Developer Options
   - Enable "USB Debugging"

3. Connect your device to your computer with a USB cable

4. When prompted on your device, allow USB debugging for your computer

### Connecting to Your Device

1. Launch the Android Automation Tool
2. In the "Device Connection" panel, click "Refresh"
3. Select your device from the dropdown list
4. Click "Connect"
5. Your device screen should now appear in the application

## Interface Overview

The application interface is divided into several sections:

- **Left Panel**: Controls for device connection, recording, playback, and settings
- **Main Display**: Shows your connected device's screen
- **Bottom Tabs**: Contains tabs for Actions, Templates, Logs, and Scheduler

## Recording Actions

### Basic Recording

1. Connect to your device
2. Click "Start Recording" in the Recording panel
3. Interact with the device screen in the application:
   - Click to perform taps
   - Click and drag to perform swipes
   - Hold for a moment to perform long press
4. Click "Stop Recording" when finished
5. Your recorded actions will appear in the Actions tab

### Adding Specific Actions

You can add specific actions without recording:

1. Click "Add Action" in the Recording panel
2. Select the action type (Tap, Swipe, Wait, etc.)
3. Fill in the parameters for the action
4. Click "OK" to add the action

### Saving and Loading Recordings

- Click "Save" to save your recorded actions to a JSON file
- Click "Load" to load previously saved actions

## Playing Back Actions

1. Make sure your device is connected
2. Adjust playback speed if needed using the Speed control
3. Click "Play" to start playback
4. Click "Stop" to interrupt playback

You can also enable loop playback by checking the "Loop playback" option.

## Working with Templates

Templates are images that the application can recognize on your device screen.

### Creating Templates

1. Connect to your device
2. Hold Ctrl and click-and-drag to select a region on the screen
3. Click "Create New" in the Templates tab
4. Choose a name and location to save the template

### Using Templates in Actions

1. Go to the Templates tab
2. Right-click on a template and select "Use in Action"
3. Configure the template matching action
4. Click "OK" to add the action

## Creating Conditional Actions

Conditional actions allow you to create if/then/else flows based on screen content:

1. Click "Add Conditional" in the Recording panel
2. Configure the condition:
   - **Template Present**: Checks if a template appears on screen
   - **Template Absent**: Checks if a template does not appear on screen
   - **Color Present**: Checks for a specific color region
   - **Pixel Color**: Checks the color of a specific pixel
3. Add actions for the "Then" branch (executed if condition is true)
4. Add actions for the "Else" branch (executed if condition is false)
5. Click "OK" to add the conditional action

## Scheduling Tasks

1. Record or load the actions you want to schedule
2. Go to the Scheduler tab
3. Click "Add Task"
4. Configure the schedule:
   - **One Time**: Run once at a specific date and time
   - **Daily**: Run every day at a specific time
   - **Weekly**: Run on selected days of the week
   - **Interval**: Run repeatedly with a specific interval
5. Set a name for the task and adjust speed if needed
6. Click "OK" to create the scheduled task

## Settings and Configuration

### Theme Settings

You can change the application theme in the Settings panel:
- Light: Bright interface
- Dark: Dark interface
- System: Follow system theme

### Capture Settings

- **Capture Interval**: Adjust how often the screen is captured (lower values = higher refresh rate but more CPU usage)
- **OpenCV Processing**: Enable/disable OpenCV image processing

## Troubleshooting

### Device Not Detected

1. Make sure USB debugging is enabled on your device
2. Disconnect and reconnect your device
3. Click "Refresh" in the Device Connection panel
4. Try restarting ADB by closing the application and running it again

### Actions Not Working Correctly

1. Make sure your device screen orientation hasn't changed
2. Check if the app on your device has updated and changed its UI
3. Try recreating templates if using template matching
4. Adjust template matching threshold if recognition is failing

### Performance Issues

1. Increase the capture interval for slower computers
2. Disable OpenCV processing if not using template matching features
3. Close other resource-intensive applications
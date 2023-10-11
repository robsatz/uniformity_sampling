import math
import numpy as np
import os
from psychopy import visual, sound, monitors, prefs, data
from psychopy.tools import monitorunittools
from psychopy.iohub import launchHubServer

def prepare_materials(self):
    '''
    Pre-loads stimuli and materials for experiment session.
    Connects to eyetracker and runs set-up procedure.
    '''
    
    print('Loading stimuli...')
    self.mon = monitors.Monitor('samplingExperiment')
    self.win = visual.Window(
        color = (-1, -1, -1),
        colorSpace = 'rgb', 
        fullscr = True, 
        units='pix', 
        allowStencil = True, 
        allowGUI = True,
        useRetina = True,
        monitor = self.mon)
    self.win.mouseVisible = False
    
    prefs.hardware['audioLib'] = ['PTB', 'sounddevice', 'pyo', 'pygame']
    loading = visual.TextStim(
        self.win, 
        text = 'Loading Stimuli...', 
        units = 'norm')
    loading.draw()
    self.win.flip()
    
    self.fixationDot = visual.Circle(
            self.win, 
            units = 'deg', 
            pos = (0,0), 
            fillColor = (1, 1, 1),
            colorSpace = 'rgb',
            radius = .5)
    self.gazeDot = visual.GratingStim(self.win, tex=None, mask='gauss', pos=(0, 0),
                              size=(1,1), color='green', colorSpace='named', units='deg')
    
    width = monitorunittools.cm2deg(self.mon.getWidth(), self.mon)
    
    nStepsHor = math.ceil(width/.87) #Field size divided by step size (in visual angles)
    stepsHor = np.linspace(-width/2,width/2,nStepsHor)
    
    height = width * 9/16 #assume aspect ratio 16:9
    nStepsVert = math.ceil(height/.87)
    stepsVert = np.linspace(-height/2,height/2,nStepsVert)
    
    coordinates = np.asarray([(x,y) for x in stepsHor for y in stepsVert]) #stores coordinates in array of shape [N,2]

    self.centerRect = visual.Rect(self.win, 
        size = (25.3, 13.3), 
        units = 'deg', 
        pos = (0,0)
        )
    self.fixationArea = visual.Rect(self.win, 
        size = (15, 13.3), 
        units = 'deg', 
        pos = (0,0)
        )

    orisSmallStd = np.random.normal(loc = 45, scale = 5, size = len(coordinates))
    orisLargeStd = np.random.normal(loc = 45, scale = 10, size = len(coordinates))
    
    centerLines = []
    periphLinesZeroStd = []
    periphLinesSmallStd = []
    periphLinesLargeStd = []
    
    for i in range(len(coordinates)):
        if self.centerRect.contains(x = coordinates[i][0], y = coordinates[i][1], units = 'deg'):
            centerLines.append(visual.Line(self.win, 
                lineWidth = 1, start = (0,-.41), end= (0,.41), 
                units = 'deg', ori = 45, pos = coordinates[i], 
                lineColor = (1,1,1), colorSpace = 'rgb'))
        else:
            periphLinesZeroStd.append(visual.Line(self.win, 
                lineWidth = 1, start = (0,-.41), end= (0,.41), 
                units = 'deg', ori = 45, pos = coordinates[i], 
                lineColor = (1,1,1), colorSpace = 'rgb')) 
            periphLinesSmallStd.append(visual.Line(self.win, 
                lineWidth = 1, start = (0,-.41), end= (0,.41), 
                units = 'deg', ori = orisSmallStd[i], pos = coordinates[i], 
                lineColor = (1,1,1), colorSpace = 'rgb')) 
            periphLinesLargeStd.append(visual.Line(self.win, 
                lineWidth = 1, start = (0,-.41), end= (0,.41), 
                units = 'deg', ori = orisLargeStd[i], pos = coordinates[i], 
                lineColor = (1,1,1), colorSpace = 'rgb')) 
    centralPatch = (-12.65,6.65,12.65,-6.65)
    
    self.center = visual.BufferImageStim(self.win, 
        stim = centerLines) 
    self.periph = {}
    self.periph['none'] = visual.BufferImageStim(self.win, stim = periphLinesZeroStd)
    self.periph['small'] = visual.BufferImageStim(self.win, stim = periphLinesSmallStd)
    self.periph['large'] = visual.BufferImageStim(self.win, stim = periphLinesLargeStd)
    
    centralCorners = [(-12.2,-7),(-12.2,7),(12.2,7),(12.2,-7)]
    self.aperture = visual.Aperture(
            self.win, 
            shape = centralCorners,
            units = 'deg')
    self.aperture.enabled = False
    self.samplingAperture = visual.Aperture(
            self.win,
            size = 5.5,
            units = 'deg')
    self.samplingAperture.enabled = False
    self.ratingText = visual.TextStim(self.win, units = 'norm', pos = (0, .6),
                    color = '#ffffff',
                    text = '''
How similar were center and periphery at the END of the trial?

1: not at all
4: completely
''')
    
    
    print('Using %s (with %s) for sounds' % (sound.audioLib, sound.audioDriver))
    self.soundLow = sound.Sound('A', octave=2, sampleRate=44100, secs=0.8, stereo=True)
    self.soundHigh = sound.Sound('A', octave=3, sampleRate=44100, secs=0.8, stereo=True)
    
    if self.simulate:
        iohub_config = {'eyetracker.hw.mouse.EyeTracker': {'name':'tracker'}}
        self.io = launchHubServer(window = self.win, **iohub_config)
        self.tracker = self.io.devices.tracker
    else:
        iohub_config = {
            'eyetracker.hw.sr_research.eyelink.EyeTracker':{
                'name': 'tracker',
                'model_name': 'EYELINK 1000 DESKTOP',
                'calibration': {
                    'auto_pace': False,
                    'screen_background_color': [0,0,0,255]
                    },
                'simulation_mode': False,
                'default_native_data_file_name': 'UIS'+self.pp,
                'runtime_settings': {
                    'sampling_rate': 500,
                    'track_eyes': 'RIGHT'
                    }
                }
            }
        self.io = launchHubServer(window = self.win, **iohub_config)
        self.tracker = self.io.devices.tracker
        self.tracker.runSetupProcedure()

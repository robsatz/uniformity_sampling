import math
import random
import numpy as np
import pandas as pd
import os
from psychopy import core, event, visual, clock, monitors, prefs, iohub, data, gui
from psychopy.tools import monitorunittools

class Session:
    from materials import prepare_materials
    def __init__(self, simulate = False, abortOption = False):
        infoDict = {'Subject ID':''}
        info = gui.DlgFromDict(infoDict)
        if info.OK:
            print(infoDict)
            self.pp = str(infoDict['Subject ID'])
        else:
            self.terminate()
        self.simulate = simulate
        self.abortOption = abortOption
        self.open_files()
        self.prepare_materials()
        self.data = []
        
    def open_files(self):
        print('creating files')
        _thisDir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(_thisDir)
        date = data.getDateStr()
        self.filename = (_thisDir + os.sep + 
            'Data'+os.sep+u'%s_%s_%s' % ('uniformity',self.pp,date) +'.csv')
        self.logfilename = (_thisDir + os.sep + 
            'Data'+os.sep+u'%s_%s_%sLOG' % ('uniformity',self.pp,date) +'.csv')
        print('Filename:', self.filename)  
        print('Logfilename:', self.logfilename)
        
    def run(self):
        self.instructions()
        self.data = []
        blocks = [Block(self,'sampling'), Block(self,'no-sampling')]
        random.shuffle(blocks)
        
        blocks[0].run()
        
        pause(self)
        
        blocks[1].run()
        
        self.store_data()
        
    def instructions(self):
        '''
        Shows instruction screen.
        '''
        instructTxt = visual.TextStim(self.win,
            '''Welcome!
We highly appreciate your participation!!
There are 3 blocks in this experiment.
Please press enter to continue.''')
        event.getKeys() #clears buffer
        while not event.getKeys(['return']):
            instructTxt.draw()
            self.win.flip()
            
    def send_msg(self, block_type, trial_index = None, txt = None):
        '''
        Sends message to eye tracker EDF file
        '''
        t = str(core.monotonicClock.getTime())
        msg = f"{t}; BLOCK{block_type}; TRIAL{trial_index}; {txt}"
        self.tracker.sendMessage(msg)
        
        
    def store_data(self):
        try:
            df = pd.DataFrame(self.data)
            print(df)
            df.to_csv(self.filename)
            print('Success! Stored data under:',self.filename)
        except:
            print('ERROR: Could not store experiment data:')
            print(self.data)
            print(self.filename)
    
    def terminate(self):
        '''
        Aborts experiment session.
        Should only be called at end of experiment.
        '''
        self.tracker.setConnectionState(False)
        self.win.close()
        self.io.quit()
        core.quit()

class Block:
    def __init__(self, session, blockType):
        self.session = session
        self.blockType = blockType
        self.practiceList = []
        self.trialList = []
        
        if self.blockType == 'no-sampling':
            
            #Determine order of practice trials
            self.practiceList = [
                Trial(self.session,'none','none'), 
                Trial(self.session,'small','none'), 
                Trial(self.session,'large','none')]
            random.shuffle(self.practiceList)
            
            #Determine order of experimental trials
            for i in range(10):
                self.trialList.append(Trial(self.session,'none','none'))
            for i in range(15):
                self.trialList.append(Trial(self.session,'small','none'))
                self.trialList.append(Trial(self.session,'large','none'))
            random.shuffle(self.trialList)
            
        elif blockType == 'sampling':
            
            #Determine order of practice trials
            self.practiceList = [
                Trial(self.session,'none','invalid'),
                Trial(self.session,'none','valid'),
                Trial(self.session,'small', 'valid'),
                Trial(self.session,'large', 'valid'),
                Trial(self.session,'small', 'invalid'),
                Trial(self.session,'large', 'invalid')]
            random.shuffle(self.practiceList)
            
            #Determine order of experimental trials
            for i in range(10):
                self.trialList.append(Trial(self.session,'none','invalid'))
                self.trialList.append(Trial(self.session,'none','valid'))
            for i in range(15):
                self.trialList.extend([
                    Trial(self.session,'small','invalid'),
                    Trial(self.session,'small','valid'),
                    Trial(self.session,'large','invalid'),
                    Trial(self.session,'large','valid')
                    ])
            random.shuffle(self.trialList)
            
        
    def run(self):
        if self.blockType == 'no-sampling':
            self.instructions(stage = 'pre-practice')
            for trial in self.practiceList:
                trial.run()
            self.instructions(stage = 'post-practice')
            
            for i, trial in enumerate(self.trialList):
                trialData = {
                    'samplingType': trial.samplingType, 
                    'periphType': trial.periphType, 
                    'blockType': self.blockType, 
                    'trialN': i+1
                        }
                self.session.send_msg(self.blockType, i+1, 'start_trial')
                trialData['rating'], trialData['n_saccades'] = trial.run()
                self.session.data.append(trialData)
                self.log_data(trialData)
                self.session.send_msg(self.blockType, i+1, 'end_trial')
        elif self.blockType == 'sampling':
            for trial in self.practiceList:
                trial.run()
            
            self.instructions(stage = 'post-practice')
            
            for i,trial in enumerate(self.trialList):
                if i == len(self.trialList)//2:
                    self.pause()
                    self.instructions(stage = 'between-blocks')
                
                trialData = {
                    'samplingType': trial.samplingType, 
                    'periphType': trial.periphType, 
                    'blockType': self.blockType, 
                    'trialN': i+1
                    }
                t = str(core.monotonicClock.getTime())
                self.session.send_msg(self.blockType, i+1, 'start_trial')
                trialData['rating'], trialData['n_saccades'] = trial.run()
                print(trialData)
                self.session.data.append(trialData)
                self.log_data(trialData)
                t = str(core.monotonicClock.getTime())
                self.session.send_msg(self.blockType, i+1, 'end_trial')
    def instructions(self, stage = None):
        if stage == 'post-practice':
            instructTxt = visual.TextStim(self.session.win, '''
You have completed the practice trials.

If you have any questions, please ask them now.
Otherwise, you may continue to the next block by pressing enter.
''')
        elif self.blockType == 'sampling':
            if stage == 'pre-practice':
                instructTxt = visual.TextStim(self.session.win,
                    '''These are your instructions for the following block:
After moving your eyes to the fixation dot, you will hear a low sound.
This indicates that you can briefly look away and back to the center as often as you would like.
Then, you will hear a higher-pitched sound.
This indicates that you should look at the center of the screen for the remainder of the trial.
Looking away from the center will abort the trial.
After each trial, you will be asked to rate how similar the orientations of the inner and outer lines were.
Make your judgment based on your perception at the END of the trial.

You will get several training trials to practice the procedure.
Please press enter to continue.''')
            elif stage == 'between-blocks':
                instructTxt = visual.TextStim(self.session.win,
                    '''The following block is the same as the last block:
After moving your eyes to the fixation dot, you will hear a low sound.
This indicates that you can briefly look away and back to the center as often as you would like.
Then, you will hear a higher-pitched sound.
This indicates that you should look at the center of the screen for the remainder of the trial.
Looking away from the center will abort the trial.

Please press enter to continue.''')
        elif self.blockType == 'no-sampling':
            instructTxt = visual.TextStim(self.session.win,
                '''Throughout all trials in the following block, please keep your gaze fixated in the center of the screen.
After each trial, you will be asked to rate how similar the orientations of the inner and outer lines were.
Make your judgment based on your perception at the END of the trial.
You will get several training trials to practice the procedure.
Please press enter to continue.''')
        event.getKeys() #clears buffer
        while not event.getKeys(['return']):
            instructTxt.draw()
            self.session.win.flip()
    def pause(self):
        '''
        Shows pause screen between blocks.
        After at least one minute, can be completed by pressing enter.
        '''
        pauseTxt = visual.TextStim(self.session.win,
            'You completed a block!\nPlease take some rest and lean back.\n\nYou can continue after one minute.')
        
        pauseClock = clock.Clock()
        
        while pauseClock.getTime() < 60:
            pauseTxt.draw()
            self.session.win.flip()
        
        continueTxt = visual.TextStim(self.session.win,
            'You may now continue.\n\nWhen you are ready, please press enter.')
        
        event.getKeys() #clears buffer
        while not event.getKeys(['return']):
            continueTxt.draw()
            self.session.win.flip()
        self.session.tracker.runSetupProcedure()
    def log_data(self, trialData):
        try:
            with open(self.session.logfilename, mode = 'a') as csv_file:
                csv_writer = csv.DictWriter(csv_file, fieldnames = trialData.keys())
                csv_writer.writerow(trialData)
            print('Stored trial data:',trialData)
        except:
            print('WARNING: Could not store trial data:',trialData)
        else:
            print(trialData)
    
    
class Trial:
    def __init__(self, session, periphType, samplingType):
        self.session = session
        self.periphType = periphType
        self.samplingType = samplingType
        
    def run(self):
        self.data = []
        self.session.soundHigh.stop() #resets sound
        self.session.soundLow.stop()
        
        self.session.win.mouseVisible = False
        self.trialClock = clock.Clock()
        event.getKeys() #clears buffer
        self.session.aperture.enabled = False
        self.session.tracker.setRecordingState(True)
        self.samplingPeriphDrawn = False
        self.fixation_dot(1.5)
        self.session.aperture.enabled = True
        self.session.tracker.clearEvents() #clears buffer
        
        n_saccades = np.array((0,0)) #holds number of saccades (index 0) and micro-saccades (index 1)
        if self.samplingType == 'none':
            aborted = self.fixation_phase(10)
        else: 
            self.session.soundLow.play()
            n_saccades += self.exploration_phase(5)
            self.session.soundHigh.play() 
            n_saccades += self.exploration_phase(1) #give subject 1s to look back to center
            aborted = self.fixation_phase(4)
        
        self.session.tracker.setRecordingState(False)
        if aborted:
            self.session.aperture.enabled = False
            txt = visual.TextStim(self.session.win,
                        'Trial invalid.\nThe trial will be repeated.',
                        color = (1,-1,-1))
            timer = clock.CountdownTimer(1)
            while timer.getTime() > 0:
                txt.draw()
                self.session.win.flip()
            return self.run() #repeat trial until successful
        else:
            return (self.rating_phase(),n_saccades)
        
    def fixation_dot(self, duration):
        self.send_msg('fixation_dot',txt = 'start_phase')
        timer = clock.CountdownTimer(duration)
        while timer.getTime() > 0:
            self.session.fixationDot.draw()
            self.session.win.flip()
        self.send_msg('fixation_dot',txt = 'end_phase')
        
    def fixation_phase(self, duration):
        self.send_msg('fixation_phase',txt = 'start_phase')
        timer = clock.CountdownTimer(duration)
        aborted = False
        self.session.tracker.getEvents() #clears buffer
        while timer.getTime() > 0 and not aborted:
            self.session.aperture.inverted = False
            self.session.center.draw()
            self.session.aperture.inverted = True
            self.session.periph[self.periphType].draw()
            
            self.session.win.flip()
            aborted = self.abort()
        self.send_msg('fixation_phase',txt = 'end_phase')
        return aborted
    def exploration_phase(self, duration):
        '''
        Administers exploration phase.
        Shows patch of periphery upon saccade out of central area.
        '''
        self.send_msg('exploration_phase',txt = 'start_phase')
        timer = clock.CountdownTimer(duration)
        n_saccades = np.array((0,0)) #number of saccades (index 0) and microsaccades (index 1)
        while timer.getTime() > 0:
            n_saccades += self.blank()
            gaze_pos = self.gazePosDeg()
            if isinstance(gaze_pos, (tuple, list)):  
                
                if self.session.centerRect.contains(gaze_pos):
                    self.session.aperture.enabled = True
                    self.session.aperture.inverted = False
                    self.session.center.draw()
                    self.session.aperture.inverted = True
                    self.session.periph[self.periphType].draw()
                    self.samplingPeriphDrawn = False
                else:  
                    self.session.aperture.enabled = False
                    if not self.samplingPeriphDrawn: #only set position of samplingAperture to gaze position after first saccade in periph
                        self.session.samplingAperture.pos = gaze_pos
                        self.samplingPeriphDrawn = True
                    self.session.samplingAperture.enabled = True
                    if self.samplingType == 'invalid':
                        self.session.periph['none'].draw() #draw no difference periphery instead of periphType
                    elif self.samplingType == 'valid':
                        self.session.periph[self.periphType].draw()
                    self.session.samplingAperture.enabled = False
                    
            self.session.win.flip()
        self.send_msg('exploration_phase', txt = 'end_phase')
        return n_saccades
    def rating_phase(self):
        self.send_msg('rating_phase', txt = 'start_phase')
        slider = visual.Slider(self.session.win, 
            ticks = (1,2,3,4),  
            labels = ['1','2','3','4'],
            pos = (0,-200),
            size = (1000,30),
            units = 'pix'
            )
        self.session.aperture.enabled = False
        
        while slider.getRating() == None:
            self.session.ratingText.draw()
            slider.draw()
            self.session.win.flip()
        
        self.send_msg('rating_phase', txt = 'end_phase')
        return slider.getRating()
    def blank(self):
        '''
        Shows blank screen if (long) saccade is detected.
        Returns number of saccades and microsaccades detected.
        '''
        n_saccades = np.array((0,0))
        saccade_starts = self.session.tracker.getEvents(event_type_id = iohub.constants.EventConstants.SACCADE_START)
        if len(saccade_starts) > 0:
            start_pos = np.array((self.gazePosDeg()))
            saccade_ends = [] 
            blink_starts = []
            while len(saccade_ends) == 0 and len(blink_starts) == 0: #wait until end of saccade or blink (blinks start with saccade event)
                saccade_ends = self.session.tracker.getEvents(event_type_id = iohub.constants.EventConstants.SACCADE_END)
                blink_starts = self.session.tracker.getEvents(event_type_id = iohub.constants.EventConstants.BLINK_START)
                
                current_pos = np.array((self.gazePosDeg()))
                if None not in current_pos and None not in start_pos:
                    saccade_length = np.linalg.norm(current_pos - start_pos) #distance of start and end point
                    if saccade_length > 1: 
                        self.session.win.flip() #blanks screen for all saccades longer than 1 degree of visual angle
            if len(saccade_ends) > 0 and None not in current_pos and None not in start_pos: 
                saccade = saccade_ends[0]
                saccade_length = np.linalg.norm(current_pos - start_pos) #distance of start and end point
                
                if saccade_length > 2:
                    n_saccades += np.array((1,0))
                else:
                    n_saccades += np.array((0,1))
        return n_saccades
    
    def abort(self):
        '''
        Returns True if gaze is in periphery, else returns False.
        Terminates session if abortOption is True and Escape was pressed.
        '''
        if self.session.abortOption and event.getKeys('escape'):
            print('session terminated')
            self.session.terminate()
        if event.getKeys(['c']):
            self.session.tracker.runSetupProcedure()
        
        #Check for saccade
        aborted = False
        
        #Wait during blinks... blinks always start with saccade event
        saccade_inits = self.session.tracker.getEvents(event_type_id = iohub.constants.EventConstants.SACCADE_START)
        if len(saccade_inits) > 0:
            saccade_ends = [] 
            while len(saccade_ends) == 0:
                saccade_ends = self.session.tracker.getEvents(event_type_id = iohub.constants.EventConstants.SACCADE_END)
                
        gaze_pos = self.gazePosDeg()
        if isinstance(gaze_pos, (tuple, list)):
            if gaze_pos == (None,None):
                gaze_in_center = True
            else:
                gaze_in_center = self.session.fixationArea.contains(gaze_pos)    
        else:
            gaze_in_center = True #do not abort when participant blinks
        
        if not gaze_in_center:
            aborted = True
            self.send_msg('fixation_phase',txt= 'ABORTED')
            
        return aborted
    
    def send_msg(self, phase, txt = None):
        '''
        Sends message to eye tracker EDF file
        '''
        t = str(core.monotonicClock.getTime())
        msg = f"{t};{phase};{txt}"
        self.session.tracker.sendMessage(msg)
    
    def gazePosDeg(self):
        '''
        Returns current gaze position in degrees of visual angle.
        '''
        posPix = self.session.tracker.getPosition()
        if isinstance(posPix, (tuple, list)):
            if posPix == (None, None):
                posDeg = posPix
            else:
                posDeg = []
                for coord in posPix:
                    posDeg.append(monitorunittools.pix2deg(coord,self.session.mon))
        else:
            posDeg = None
        return posDeg

session = Session(simulate = True, abortOption = True)
session.run()

#Author-Ian Rist
#Description-AI Overlord Centric CAD

# Known Issues
# Most of these are to do with there not being enough examples using the Fusion API
# I might go and make a bunch of programs with correct examples and put them on github to help with some of this
# It literally cant dimension anything
# It dose not understand units correctly, if you say '5 in', '5 mm', or '5 cm' it will just put in 5 which fusion takes as cm
# However if you put in '5cm' with no space it will convert that into meters and input 0.05 even though the input field is in cm
# If the number of tokens is too high for the complexity of your question (it should never be higher than 512, and 256 is a lot even) then it will try and make a addin, we want it to try and make a script
# If the number of tokens is too high the query will take too long and fusion will shit the bed, I have to make a custom event handler to address this
# If it keeps running on or the temperature is too high it will try and use methods or properties of some other random object (usually happens with constructors for shape perimitives)
# Updating the preview every time you type a character into the box is shit and has to be reworked
# The API key gets flushed every time

# Ideas
# Include a library for converting units to make it convert units right that would have examples and make it understand that we want cm



import adsk.core, adsk.fusion, adsk.cam, traceback
import json, os
import urllib.request as url
from pathlib import Path
import openai
import time
import datetime
from os import path
#from dotenv import load_dotenv
#import pandas
#import numpy

_app: adsk.core.Application = None
_ui: adsk.core.UserInterface = None
_handlers = []

#load_dotenv()

def getENV():
    #envvars = os.getenv('OPENAI_API_KEY')
    os.environ.get('OPENAI_API_KEY')
    if envvars and envvars != "":
        return envvars
    return None

def setENV(key):
    #os.system("SETX {0} {1} /M".format("OPENAI_API_KEY",key))
    #os.environ.putenv("OPENAI_API_KEY", key)
    os.environ["OPENAI_API_KEY"] = key

def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface
        

        # Create the command definition for the feature create.
        CodexFeatureCmdDef = _ui.commandDefinitions.addButtonDefinition('irCodexFeature', 'Codex Feature', 'Create Feature Using Codex', 'Resources/Button')

        # Add the create button the user interface.
        createPanel = _ui.allToolbarPanels.itemById('SolidCreatePanel')

        # Places the command right where we want it
        cntrl = createPanel.controls.addCommand(CodexFeatureCmdDef, "SeparatorAfter_EmbossCmd", False)

        # This makes it end up on the hotbar
        cntrl.isPromoted = True
        cntrl.isPromotedByDefault = True

        #

        # Connect the handler to the command created event for the holesaw create.
        onCommandCreated = CodexCreateCommandCreatedHandler()
        CodexFeatureCmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)

    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class CodexWebHandler():
    def __init__(self, key):
        self.CodexAPIKey = key
        self.setAPIKey(key)

    # Calls Codex to get inspection list
    def refresh(self, prompts, temp, tok):
        try:
            response = openai.Completion.create(
              engine="davinci-codex",
              prompt=prompts,
              temperature=temp,
              max_tokens=tok,
              top_p=1.0,
              frequency_penalty=0.0,
              presence_penalty=0.0,
              stop=["\"\"\""]
            )
            return response.get("choices")[-1].get("text")
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            return None

    def setAPIKey(self, key):
        openai.api_key = key
        self.CodexAPIKey = key

    # Test an API Key
    def checkNewAPIKey(self, key):
        if key:
            return True
        return False

    # Test API Key
    def checkAPIKey(self):
        return self.checkNewAPIKey(self.CodexAPIKey)

def Dump(outs):
    # Get the current time
    now = datetime.datetime.now()
    # Get the current time and date
    time_date = now.strftime("%Y-%m-%d %H:%M")
    # Get the current directory
    current_dir = os.getcwd()
    # Get the output directory
    output_dir = os.path.join(current_dir, "outputs")
    # Get the output file name
    output_file = os.path.join(output_dir, "output_" + str(now.hour) + "_" + str(now.minute) + ".py")
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # Open the output file
    with open(output_file, "w") as f:
        # Add the time and date to the file
        f.write("#Time and date: " + time_date)
        f.write("\n\n\n")
        f.write(outs)
    # Close the file
    f.close()
    return str(output_dir)

class CodexCreateCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command
            inputs = cmd.commandInputs

            # Idk what this does so im not going to touch it
            des: adsk.fusion.Design = _app.activeProduct

            # Get the Codex API Key
            CodexKey = getENV()
            if not CodexKey:
                # Tell them to set their key
                _ui.messageBox('You have no Codex API Key Saved\nPlease Input your Codex API Key')

            # For Debug
            #_ui.messageBox(str(os.environ))

            # Init script and get latest machine data
            mm = CodexWebHandler(CodexKey)

            startingtext = "\"\"\"\n\n\"\"\""

            # Make the inputs
            codexCmd = inputs.addTextBoxCommandInput('Codexcmd', 'Codex Command:', startingtext,10, False)
            sendCommand = inputs.addBoolValueInput('sendCmd', 'Send Command', False)
            sendCommand.isFullWidth = True

            inputs.addFloatSliderCommandInput('temp', 'Temprature', 'cm', 0.0, 1.0)
            inputs.addIntegerSliderCommandInput('tokens', 'Numbet of tokens', 196, 2048)


            # Add an option to clear the API Key
            clearkey  = inputs.addBoolValueInput('clearkey', 'Clear Codex API Key', False)
            clearkey.isFullWidth = True

            # Make them set or reset the key
            CodexAPIKey = inputs.addTextBoxCommandInput('Codexkey', 'Codex API Key:', '',1, False)
            setkey = inputs.addBoolValueInput('setkey', 'Set Key', False)
            setkey.isFullWidth = True

            # Check if they have a valid key
            if mm.checkAPIKey() == False:
                # Hide our Table
                codexCmd.isVisible = False
                
                # Add a Refresh Button
                sendCommand.isVisible = False
                
                # Add an option to clear the API Key
                clearkey.isVisible = False

            else:
                # Make them set or reset the key
                CodexAPIKey.isVisible = False
                setkey.isVisible = False


            onExecutePreview = CreateExecutePreviewHandler()
            cmd.executePreview.add(onExecutePreview)
            _handlers.append(onExecutePreview)

            onExecute = CreateExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)

            onActivate = CreateActivateHandler(mm)
            cmd.activate.add(onActivate)
            _handlers.append(onActivate)

            onInputChanged = CreateInputChangedHandler(mm)
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)

        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class CreateActivateHandler(adsk.core.CommandEventHandler):
    def __init__(self, mm):
        super().__init__()
        self.mm = mm
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)

            # Gets the selected uid from the current args
            #uid = eventArgs.

            # Gets the data needed from Codex
            #inspectionPath, inspectionData = self.mm.getDat(uid)

            # Code to react to the event.
            ShowMessage('In MyActivateHandler event handler.')
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def addContext(cmd):
    prefix = '''import adsk.core, adsk.fusion, adsk.cam, traceback
    import json, os
    import urllib.request as url
    from pathlib import Path

    # Default units are cm

    _app: adsk.core.Application = None
    _handlers = []

    
def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface
'''
    return prefix + cmd

def niceres(res):
    cleanres = str(res).replace("&quot;&quot;&quot;","\"\"\"").replace("&quot;", "").replace("        ", "")
    return cleanres

def runnnn(cmddd):
    try:
        exec(cmddd)
        return True
    except:
        _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class CreateInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self, mm):
        super().__init__()
        self.mm = mm
    def notify(self, args):
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            inputs = eventArgs.inputs
            cmdInput = eventArgs.input
            
            if cmdInput.id == "sendCmd":
                cmd = inputs.itemById('Codexcmd')
                cmdtext = cmd.text
                nicecmd = addContext(cmdtext)
                temp = inputs.itemById('temp').valueOne
                tokens = inputs.itemById('tokens').valueOne
                response = self.mm.refresh(nicecmd, temp, tokens)
                cleanres = niceres(cmdtext) + niceres(response)
                cmd.text = cleanres
            
            if cmdInput.id == "setkey":
                newkey = inputs.itemById('Codexkey').text
                if self.mm.checkNewAPIKey(newkey):
                    self.mm.setAPIKey(newkey)
                    setENV(newkey)
                    inputs.itemById('setkey').isVisible = False
                    inputs.itemById('Codexkey').isVisible = False
                    inputs.itemById('Codexcmd').isVisible = True
                    inputs.itemById('sendCmd').isVisible = True
                    inputs.itemById('clearkey').isVisible = True
                    _ui.messageBox('Set API Key')
                else:
                    _ui.messageBox('Bad API Key')
            if cmdInput.id == "clearkey":
                newkey = ""
                self.mm.setAPIKey(newkey)
                setENV(newkey)
                inputs.itemById('setkey').isVisible = True
                inputs.itemById('Codexkey').isVisible = True
                inputs.itemById('Codexcmd').isVisible = False
                inputs.itemById('sendCmd').isVisible = False
                inputs.itemById('clearkey').isVisible = False
                _ui.messageBox('Cleared API Key')
            else:
                pass
          
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class CreateExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            cmd = eventArgs.command
            inputs = cmd.commandInputs
            #_ui.messageBox(inputs)
            if True:#cmdInput.id == "Codexres":
                returnbox = inputs.itemById('Codexcmd')
                retstr = niceres(returnbox.text)
                yo = runnnn(retstr)

        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class CreateExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            cmd = eventArgs.command
            inputs = cmd.commandInputs
            
            returnbox = inputs.itemById('Codexcmd')
            retstr = niceres(returnbox.text)
            #write to file
            fileloc = Dump(addContext(retstr))
            yo = runnnn(retstr)
            _ui.messageBox(fileloc)

        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def ShowMessage(message: str):
    textPalette: adsk.core.TextCommandPalette = _ui.palettes.itemById('TextCommands')
    if textPalette:
        textPalette.writeText(message)

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        createPanel = ui.allToolbarPanels.itemById('SolidCreatePanel')
        cmdCntrl = createPanel.controls.itemById('irCodexFeature')
        if cmdCntrl:
            cmdCntrl.deleteMe()

        CodexFeatureCmdDef = ui.commandDefinitions.itemById('irCodexFeature')
        if CodexFeatureCmdDef:
            CodexFeatureCmdDef.deleteMe()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

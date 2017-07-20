from aqt import mw
from aqt.deckconf import DeckConf
from anki.hooks import addHook, wrap
from anki.sound import Recorder

from PyQt4 import QtCore, QtGui

import datetime
import os

# TODO: Hook to the again/hard/good/easy selection part
# TODO: Record again/hard/good/easy as part of the filename

recorder = Recorder()
is_recording = False

def get_configuration(did, key, default):
    configuration = mw.col.decks.confForDid(did)
    if 'addons' not in configuration:
        return default

    if 'anki_recorder' not in configuration['addons']:
        return default

    if key not in configuration['addons']['anki_recorder']:
        return default

    return configuration['addons']['anki_recorder'][key]

def get_target_directory(did):
    return get_configuration(did, 'directory', 'anki_recorder')

def get_record_audio(did):
    return get_configuration(did, 'record_audio', False)

def should_record_audio():
    card = mw.reviewer.card.__dict__
    did = str(card['did'])
    return get_record_audio(did)

# Start recording when a question is shown
def onShowQuestion():
    if not should_record_audio():
        return

    recorder.start()
    is_recording = True

# Stop recording when the answer is shown
def onShowAnswer():
    if not should_record_audio():
        return

    is_recording = False
    recorder.stop()
    recorder.postprocess(True)
    recorded_file = recorder.file()
    filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S') + '.mp3'

    card = mw.reviewer.card.__dict__
    did = str(card['did'])
    cid = str(card['id'])

    recording_directory = os.path.join(get_target_directory(did), did, cid)
    if not os.path.exists(recording_directory):
        os.makedirs(recording_directory)

    os.rename(recorded_file, os.path.join(recording_directory, filename))

# Make sure to stop the recorder is we leave the reviewer
def onReviewCleanup():
    if is_recording:
        recorder.stop()

def test():
    print(target_directory)

addHook('showQuestion', onShowQuestion)
addHook('showAnswer', onShowAnswer)
addHook('reviewCleanup', onReviewCleanup)

# Add a new tab to the deck option window to configure the addon
def addTabToDeckOptions(self):
    if not hasattr(self, 'addons'):
        self.addons = {}

    self.addons['anki_recorder'] = {}

    tab = QtGui.QWidget()
    vertical_layout = QtGui.QVBoxLayout(tab)
    grid_layout = QtGui.QGridLayout()
    vertical_layout.addLayout(grid_layout)

    checkbox_record_audio = QtGui.QCheckBox(tab)
    checkbox_record_audio.setText('Record audio')
    grid_layout.addWidget(checkbox_record_audio, 0, 0, 1, 1)

    self.addons['anki_recorder']['record_audio'] = checkbox_record_audio

    label_directory = QtGui.QLabel(tab)
    label_directory.setText('Audio file storage location')
    grid_layout.addWidget(label_directory, 1, 0, 1, 1)

    textbox_directory = QtGui.QLineEdit(tab)
    grid_layout.addWidget(textbox_directory, 1, 1, 1, 1)

    self.addons['anki_recorder']['directory'] = textbox_directory

    self.form.tabWidget.addTab(tab, 'Anki Recorder')

# Update the tab content when a new configuration is loaded
def updateConfigurationTab(self):
    self.addons['anki_recorder']['record_audio'].setChecked(get_record_audio(self.deck['id']))
    self.addons['anki_recorder']['directory'].setText(get_target_directory(self.deck['id']))

# Update deck configuration
def saveConfiguration(self):
    self.conf.setdefault('addons', {}).setdefault('anki_recorder', {})

    form = self.addons['anki_recorder']
    anki_recorder_configuration = self.conf['addons']['anki_recorder']

    anki_recorder_configuration['record_audio'] = form['record_audio'].isChecked()
    anki_recorder_configuration['directory'] = form['directory'].text()

DeckConf.setupConfs = wrap(DeckConf.setupConfs, addTabToDeckOptions, 'before')
DeckConf.loadConf = wrap(DeckConf.loadConf, updateConfigurationTab)
DeckConf.saveConf = wrap(DeckConf.saveConf, saveConfiguration, 'before')

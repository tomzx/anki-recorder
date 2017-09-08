from aqt import mw
from aqt.reviewer import Reviewer
from aqt.deckconf import DeckConf
from anki.hooks import addHook, wrap
from anki.sound import Recorder

from PyQt4 import QtCore, QtGui

import datetime
import os

# TODO: Add support for ctrl+z?

recorder = None
filename = None
recording_directory = None

def log(message):
    is_debug = False

    if not is_debug:
        return

    now = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S.%f')
    card = mw.reviewer.card.__dict__
    cid = str(card['id'])
    with open('anki_recorder.log', 'a') as file:
        file.write('[' + now + '][cid=' + cid + ']' + message + '\n')

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
def on_show_question():
    global recorder
    global filename
    global recording_directory

    filename = None
    recording_directory = None

    if recorder:
        log('[on_show_question][{}] Stop recording'.format(recorder.thread.ident))
        recorder.stop()
        recorder = None

    if not should_record_audio():
        return

    recorder = Recorder()
    recorder.start()
    log('[on_show_question][{}] Start recording'.format(recorder.thread.ident))

# Stop recording when the answer is shown
def on_show_answer():
    global recorder
    global filename
    global recording_directory

    if not should_record_audio():
        return

    log('[on_show_answer][{}] Stop recording'.format(recorder.thread.ident))
    recorder.stop()
    recorder.postprocess(True)
    recorded_file = recorder.file()
    recorder = None
    filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S') + '.mp3'

    card = mw.reviewer.card.__dict__
    did = str(card['did'])
    cid = str(card['id'])

    if not os.path.exists(recorded_file):
        log('[on_show_answer] Could not find recorded file {}'.format(recorded_file))

    recording_directory = os.path.join(get_target_directory(did), did, cid)
    if not os.path.exists(recording_directory):
        os.makedirs(recording_directory)

    old_path = recorded_file
    new_path = os.path.join(recording_directory, filename)
    log('[on_show_answer] Renaming file {} to {}'.format(old_path, new_path))
    os.rename(old_path, new_path)

# Make sure to stop the recorder is we leave the reviewer
def cleanup_recorder():
    global recorder

    if recorder:
        log('[cleanup_recorder][{}] Stop recording'.format(recorder.thread.ident))
        recorder.stop()
        recorder = None

addHook('showQuestion', on_show_question)
addHook('showAnswer', on_show_answer)
# If the user leaves through going back to the main page
addHook('reviewCleanup', cleanup_recorder)
# If the user leaves through closing the app
addHook('unloadProfile', cleanup_recorder)

# Add a new tab to the deck option window to configure the addon
def add_tab_to_deck_options(self):
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
def update_configuration_tab(self):
    self.addons['anki_recorder']['record_audio'].setChecked(get_record_audio(self.deck['id']))
    self.addons['anki_recorder']['directory'].setText(get_target_directory(self.deck['id']))

# Update deck configuration
def save_configuration(self):
    self.conf.setdefault('addons', {}).setdefault('anki_recorder', {})

    form = self.addons['anki_recorder']
    anki_recorder_configuration = self.conf['addons']['anki_recorder']

    anki_recorder_configuration['record_audio'] = form['record_audio'].isChecked()
    anki_recorder_configuration['directory'] = form['directory'].text()

DeckConf.setupConfs = wrap(DeckConf.setupConfs, add_tab_to_deck_options, 'before')
DeckConf.loadConf = wrap(DeckConf.loadConf, update_configuration_tab)
DeckConf.saveConf = wrap(DeckConf.saveConf, save_configuration, 'before')

# Append the ease to the filename
def on_answer_card(self, ease):
    # Taken from Reviewer._answerCard
    if self.mw.state != "review":
        # showing resetRequired screen; ignore key
        return
    if self.state != "answer":
        return
    if self.mw.col.sched.answerButtons(self.card) < ease:
        return

    if not filename:
        return

    recorded_file = os.path.join(recording_directory, filename)
    new_filename = os.path.splitext(filename)[0] + ' ' + str(ease) + '.mp3'
    os.rename(recorded_file, os.path.join(recording_directory, new_filename))

Reviewer._answerCard = wrap(Reviewer._answerCard, on_answer_card, 'before')
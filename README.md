# Anki Recorder
`Anki Recorder` is a small add-on for [Anki](https://apps.ankiweb.net/) which records the audio from when a question is displayed until the answer is shown. The main purpose of this add-on is to record progress for users using Anki as a tool to learn languages.

## Getting started
* Clone the git repository to your Anki add-on directory `git clone https://github.com/tomzx/anki-recorder anki_recorder`
* Create a file in the addons directory called `anki_recorder.py` with the following content:
```py
import anki_recorder
```

In the deck options, a new tab will be added called "Anki Recorder". There you can set whether you want the decks using the given deck options to have their audio recorded, as well as where the audio files should be saved. If the path is not absolute, files will be saved in the user's collection.media directory.

## License
The code is licensed under the [MIT license](http://choosealicense.com/licenses/mit/). See [LICENSE](LICENSE).

# Urtext Package for Sublime Text

## What Urtext Is

Urtext is a Python library wrapping and syntax, parser and compiler for plaintext writing. It is for prose, research, documentation, journaling, project organization, notetaking, and any other writing or information management that can be done in text form.

The core library has no user interface and requires a text editor implementation. This package is an implementation for desktop (PC/Mac/Linux) using [Sublime Text](https://www.sublimetext.com/.

## Documentation

A documentation both of Urtext and this Sublime Text implementation is at https://urtext.co/.

## Installation

For experienced Sublime Text users, note that this package is no longer updated on [Package Control](https://urtext.co/installation-and-setup/sublime-text/installation-and-setup-in-sublime-text/). It should be installed manually.


### Basic (most users):

1. Download the Urtext package as a .ZIP file.
2. Unzip the file
3. Rename the folder to `Urtext` (this step is required)
4. Move the folder to the Sublime Text Packages folder:
- Windows: `%APPDATA%\Sublime Text`
- Mac: `~/Library/Application Support/Sublime Text/Packages` On Mac, the ~/Library directory is hidden by default. To navigate there, select the Go ▶ Go to Folder menu item in Finder, and type in `~/Library`.
- Linux: `~/.config/sublime-text`

### With Git:

Install using Git if you are developer, want to contribute, want to pull updates without re-downloading, or want to be able to switch to the development branch.

1. Clone this repository into the Sublime Text Packages folder. (See above for the folder location depending on operating system.)
2. Rename the folder `Urtext` (this step is required)

## Getting Started

- Restart Sublime Text
- Press ⌘/Ctrl + ⇧ + P to access the Command Pallete. 
- Start typing "Urtext: Create Starter Project" and select it from the dropdown
- Select a folder for the starter project
- The project will open and display its start page.

## Questions and Issues

Questions and issues may be submitted either to https://urtext.co/support/ or to https://github.com/nbeversl/urtext-sublime/issues.

## Versioning

[SemVer](http://semver.org/).

## License

Urtext is licensed under the GNU 3.0 License.

## Acknowledgments

Hat tip to @c0fec0de for [anytree](https://github.com/c0fec0de/anytree).


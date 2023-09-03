# PyPew

PyPew is a Flask app that helps you generate pew sheets for services
using texts from the Book of Common Prayer. You can specify the date
of your service, the Feast from which the texts should be used, the
hymns to be sung, as well as other details such as the name of the
priest, and all this information is assembled into a web page or .docx
file for editing or printing.

There is a demonstration deployment at
[https://pypew.herokuapp.com](https://pypew.herokuapp.com) but it is
also possible to run PyPew as a desktop app.


## Running as a Flask app

1. Edit the variables in `.env` to your taste (the defaults should be
   reasonable)
2. Install the requirements: `pip install -r requirements.txt`
3. `python pypew.py`

This should start up the Flask server as well as automatically opening
up your browser to `http://localhost:5000`.


## Packaging

It is also possible to compile binaries for PyPew that can be run
without needing Python to be setup.

### Windows

  1. Run `build.bat` to create a folder in `dist/pypew`, containing the
     executable `pypew.exe` as well as all the necessary files and DLLs.
     (This is rather large as it includes an entire Python distribution
     as well as packages like Pandas; it comes to around 100MB in
     total.)

  2. If desired, use [Advanced Installer](https://advancedinstaller.com/)
     to create an .msi that will install PyPew into the 'Program Files'
     directory, together with shortcuts in the Start Menu.

### MacOS

The `build.sh` script runs PyInstaller to build `dist/pypew.app`, which
may then be put into your 'Applications' directory.


## Customising PyPew

### Feast dates and texts

The texts, dates and such of all the Feasts are stored in the CSV file
`data/feasts.csv`. This file should have the following column headers:
```csv
name,month,day,coeaster,coadvent,introit,collect,epistle_ref,epistle,gat,gradual,alleluia,tract,gospel_ref,gospel,offertory,communion
```
---
| Column      | Type          | Definition                                                          |
|-------------|---------------|---------------------------------------------------------------------|
| name        | str           | Name of the Feast                                                   |
| month       | Optional[int] | Month of the Feast (if fixed date)                                  |
| day         | Optional[int] | Day of the Feast (if fixed date)                                    |
| coeaster    | Optional[int] | Number of days since Easter (if moving with Easter)                 |
| coadvent    | Optional[int] | Number of days since Advent Sunday (if moving with Advent)          |
| introit     | str           | Text of the Introit Proper                                          |
| collect     | str           | Collect for the Feast. May be combined with those for other Feasts. |
| epistle_ref | str           | Reference for the Epistle reading ('Visigoths 12:25')               |
| epistle     | str           | Text of the Epistle reading                                         |
| gat         | str           | Which of the Gradual, Alleluia and Tract Propers should be sung     |
| gradual     | str           | Text of the Gradual Proper (if present)                             |
| alleluia    | str           | Text of the Alleluia Proper (if present)                            |
| tract       | str           | Text of the Tract Proper (if present)                               |
| gospel_ref  | str           | Reference for the Gospel reading ('Matthew 21:17')                  |
| gospel      | str           | Text of the Gospel reading                                          |
| offertory   | str           | Text of the Offertory Proper                                        |
| communion   | str           | Text of the Communion Proper                                        |

The Feasts that move with Easter (including all of Lent and Trinity)
should have a value in the `coeaster` column. The Advent Feasts (Advent
I, II, III and IV) should have a value in the `coadvent` column.
Otherwise the date of the Feast should be given in the `month` and `day`
columns. (There are a couple of special cases, like Remembrance Sunday
which does not fall on a specific date but is instead the nearest Sunday
to 11 November; this is not yet handled properly.)


## Licensing

PyPew is licensed under the MIT License.

Distributions of the PyPew include extracts from the Book of Common
Prayer. Extracts from The Book of Common Prayer, the rights of which are
vested in the Crown, are reproduced by permission of the Crown's
patentee, Cambridge University Press.

Information about hymns is courtesy of [Hymnary.org](https://hymnary.org).

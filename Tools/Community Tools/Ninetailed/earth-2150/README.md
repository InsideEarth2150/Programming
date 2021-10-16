These are a few tools I've written to dig around in the Earth 2150 data files. If you'd like to follow along with my reverse engineering adventures, you can find the story and technical details over on [my blog](https://ninetailed.net/reverse-engineering-earth-2150.html).

Stuff of interest includes:

## PAR compiler/decompiler
Many of the game's definitions, including unit stats and tech tree, are stored in a file called `Parameters\EARTH2150.par` contained in the `Parameters.wd` or `Update21.wd` files. These scripts are intended for manipulating this PAR file. These are of *alpha* quality - they work on a basic level, but some features are incomplete and they don't handle error conditions well.

### par2csv.py
A Python script that reads a PAR file and dumps its contents out to a series of CSV files. This can handle anything in the base files for Earth 2150, The Moon Project, or Lost Souls, but is untested on mods and unofficial patches.

To use the script, place it and the PAR file you want to extract in the same directory and run it through Python. Alternatively, you may pass the PAR file's path in as a command line argument, and CSV files will be placed in the current working directory.

Documentation of what each field does to follow.

### csv2par.py
The reverse process. This reads the CSV files produced by par2csv – and *only* those files, other CSV file names are ignored – and produces a PAR file from the data. Both CSV input files and PAR output file will be sourced from the current working directory.

This PAR file can be placed in the `Parameters` directory of your game install directory, which you may need to create, and the game will read it in preference over the versions contained in the WD files.

### Known limitations
Object types are hard-coded. I suspect it may be possible to modify the game to include other object types, but this is beyond my current level of knowledge. As such, if new object formats are included, these scripts will almost certainly crash.

Running par2csv and csv2par in sequence without changing the CSV files will produce a PAR file of identical size that contains the same objects, but will likely *not* be bit-for-bit identical due to limitations in how the parameters.csv file is generated. Nonetheless, this file will work the same in-game.

All non-text fields are represented as raw decimal integers this has several effects:

Some fields expect floating point values. These are not currently supported. If you want to change these fields, you will need to convert them bitwise from a 32-bit float to a 32-bit integer by hand, e.g. 1.0 becomes 1065353216.

Some fields expect a bit-masked value. Again, this will require manual conversion of the values to/from base 2 or 16 for working on them.

Class IDs, where present, are also shown as raw numbers. Ideally this should work with their names instead.

## wdfile.py
This is mostly an indulgence of my own curiosity. It will read all WD files in a directory (hard coded in the script) and dump out all the file contents into that same directory. There are better tools available for working with WD files.

## tex2png.py
This is a proof-of-concept that turns TEX files into PNG images. Requires PIL: `pip install Pillow`

Don't actually use this. Other modders have done this better, I just independently reversed the format to satisfy my own curiosity.

* Credit: Ninetailed
* Web Source: https://ninetailed.net/reverse-engineering-earth-2150.html
* Git Source: https://git.ninetailed.net/terrana/earth-2150

# TSPOOFER
Programmed by: *Dante Signal31 (dante.signal31@gmail.com)*

This program stores file timestamps under a file tree in order to restore them after file modification.

### Usage

    $ tspoofer *arguments*

         -b <directory to backup> --------> Directory to backup its file timestamps.
         -r <directory to restore> -------> Directory to restore its timestamps.
         -d <directory to use> -----------> Directory where data gathered by TSpoofer is stored. (OPTIONAL)
         -c <directory> ------------------> Clean tspoofer footprint about directory. '*' means every footprint.
         -h | --help --------------> Print this text.

### Examples
Storing directory timestamps:

    $ tspoofer -b /directory/sudirectory -d /tmpdir/tmpsubdir

Restoring timestamps:

    $ tspoofer -r /directory/sudirectory -d /tmpdir/tmpsubdir

Deleting temporary files:

    $ tspoofer -c '*' -d /tmpdir/tmpsubdir

## DISCLAIMER
I made this tool long time ago to demostrate [timestamp forgery](https://www.dlab.ninja/2011/10/timestamps-falsification.html). 
I've not tested since them, so it can be entirely broken. Use it at your own risk.
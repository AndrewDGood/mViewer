#!/home/agood/agooddev.com/env/bin/python -i


# This is a simple command-line utility to get mViewer Python started
# It just handles the basics: Get the image(s) up with optional overlays

import agMontage.mViewer as mv
import argparse
import sys
import os


# Custom usage message

def msg(name=None):                                                            
    return '''mView.py -g GRAY.fits | -c BLUE.fits GREEN.fits RED.fits
         [-C CATALOG.tbl] [-I IMAGES.tbl] [-G COORD_SYS [EQUINOX]]
         (overlays can be repeated)
        '''

# Command-line arguments

parser = argparse.ArgumentParser(description='mVIEWER: Interactive Astronomical Image Display.', usage=msg())

parser.add_argument('-d', '--debug', help='Turn on debugging.', action='store_true')
parser.add_argument('-s', '--server', help='Start in server (remote browser) mode.', action='store_true')

parser.add_argument('-g', '--gray',    nargs=1,   help='Grayscale/pseudocolor FITS file')
parser.add_argument('-c', '--color',   nargs=3,   help='Blue, green, red full color FITS files')
parser.add_argument('-C', '--catalog', nargs=1,   help='Source table with sky positions', action='append')
parser.add_argument('-I', '--images',  nargs=1,   help='Image metadata table', action='append')
parser.add_argument('-G', '--grid',    nargs='*', help='Coordinate system for overlay grid', action='append')

try:
    args = parser.parse_args()
except SystemExit:
    os._exit(0)


if args.gray is None and args.color is None:
    print '\nERROR: You must choose one of grayscale (one image) or full color (three images). See "mView.py --help"\n'
    os._exit(0)

if args.gray and args.color:
    print '\nERROR: You must choose either grayscale (one image) or full color (three images).\ See "mView.py --help"n'
    os._exit(0)


# Start mViewer

viewer = mv.mViewer()


# Turn on debugging, if desired

viewer.debug = args.debug


# Set "server" mode.  The Python code will be started but rather than trying to start a captive
# browser, the URL for connecting will be printed out, so the user can paste it into a browser
# of their choice.  This is often used where the browser is on a different machine (e.g. office
# desktop or home computer).

viewer.serverMode = args.server


# Set the image or images

if args.gray:
    viewer.set_color_table(1)
    viewer.set_gray_file(args.gray[0])
 
else:
    viewer.set_blue_file (args.color[0])
    viewer.set_green_file(args.color[1])
    viewer.set_red_file  (args.color[2])


# Add any coordinate grids

if args.grid:

    ngrid = len(args.grid)

    for i in range(0, ngrid):

       viewer.set_current_color("blue")   

       if len(args.grid[i]) == 1:
           csys = args.grid[i][0]
       else:
           csys = args.grid[i][0] + " " + args.grid[i][1]

       viewer.add_grid(csys)
    

# Add any catalogs

if args.catalog:

    ncatalog = len(args.catalog)

    for i in range(0, ncatalog):

        viewer.set_current_color("yellow")   
        viewer.set_current_symbol(1.0, "circle")  

        viewer.add_catalog(args.catalog[i][0], '', '', '') 


# Add any image outlines

if args.images:

    nimages = len(args.images)

    for i in range(0, nimages):

        viewer.set_current_color("red")   

        viewer.add_img_info(args.images[i][0]) 


# Fire up the display

viewer.init_browser_display()


# Additional debugging flags, which we couldn't 
# turn on until now

viewer.thread.debug         = args.debug
viewer.thread.handler.debug = args.debug


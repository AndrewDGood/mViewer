#---------------------------------------------------------------------------------
#  Montage Viewer Python Application                                                    
#---------------------------------------------------------------------------------


from threading import Thread

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.template

import sys
import webbrowser
import subprocess
import os
import errno
import sys
import tempfile
import shutil
import random
import hashlib
import shlex
import math
import json


from pkg_resources import resource_filename

 
# This file contains the main mViewer object and a few support objects:
# 
#    mvStruct       --  Parser for Montage executable module return structures
#    mvViewOverlay  --  Data structure for image overlays info
#                        (grids, catalogs, etc.)
#    mvViewFile     --  Data structure for FITS file display info
#    mvView         --  Data structure for an mViewer view (includes instance 
#                       of the previous two objects)
#    mvMainHandler  --  Event handler for Tornado web service toolkit 
#                        (main index.html request)
#    mvWSHandler    --  Event handler for Tornado web service toolkit 
#                        (support file requestss; e.g., JS files)
#    mvThread       --  Extra thread for browser communications
#    mViewer        --  Main object

# Python does not support forward referencing, that is, the ability to
# refer to a class in source code before it has actually been defined.
# So the simplest way to accomodate this is to define classes in
# "reverse order", as above.

# mViewer is the main object and contains all the code that specifies
# how the picture we see of the sky is to be generated (and how interactive
# events like zooming are to be handled).  It is the main thread the user
# talks to interactively.  

# The actual specification of the "view" (how the picture is to look) 
# held in the mvView object, which contains all sorts of data values
# (like the grayscale color table name) but no processing methods beyond
# the basic "print me out" __str__ and __repr__ code.  mvView in turn
# uses a couple of specialized containers: mvViewFile (for specifying
# an image file and its attributes) and mvViewOverlay (for specifying
# various layers drawn on top of the image).

# At startup, mViewer spawns of a second thread (mvThread), whose sole
# purpose is to handle browser (our display surface) interactions.  It
# picks a port at random and fires up a tornado.Application object (web
# server listening on that port) and points it at mvMainHandler and 
# mvWSHandler, two objects which deal with requests from the browser
# (plus a third tornado built-in for requesting simple file downloads).
# It then fires up a browser instance (which browser is configurable) 
# and points it at "localhost" and the above port.

# mvMainHandler is the mechanism where the basic "index.html" file is
# gotten to the browser.  This is the only "page" the browser is ever 
# going to display and contains all the Javascript needed to be the
# other half of our user interface.

# The rest of the user interface interaction is handled by mvWSHandler.
# It and the Javascript in the browser send messages and data back and
# forth whenever anything needs to be done.  The events driving this
# interaction can be initiated in the browser (user clicks the "zoom in"
# button) or by the user at the mViewer "prompt" (basic python 
# user interaction).

# All requests for changes to the view end up in the mViewer code, which
# uses various Montage modules on the back end (mExamine, mSubimage,
# mShrink, mViewer) to do the data management.  Currently, this is 
# handled through subprocess.Popen() infrastructure, though the Montage
# Project is currently working on the Montage modules directly 
# callable in Python.  Montage modules return a structure text response
# and the final code here, mvStruct, is used to parse this and turn it
# into a Python data object.


#---------------------------------------------------------------------------------
#  CLASS RELATIONSHIPS
#
#
#             +-> mvView +-> mvViewFiles
#             |          |                      (Data structures)
#             |          +-> mvViewOverlays
#             |
#             |
#             |
#             +-> mvThread +-> webbrowser.open()     (Browser interface)        --+         
#             |            |                                                      |
#             |            |                                                      V
#             |            |                                                      
#             |            |                                                 ------------
#             |            |                                                [  Browser:  ]
#     mViewer +            +-> tornado.Application +-> mvMainHandler   <=>  [            ]
#             |                                    |                        [  mViewer   ]
#             |                                    +-> mvWSHandler     <=>  [ Javascript ]
#             |                                                              ------------
#             |
#             |
#             |
#             |                            (Montage Applications)       
#             |                              ------------------     
#             +-> subprocess.Popen()  <=>   [                  ]
#             |                             [     mExamine     ]
#             |                             [     mSubimage    ]
#             |                             [     mShrink      ]
#             |                             [     mViewer      ]
#             +-> mvStruct                  [                  ]
#                                            ------------------
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
#  COMMUNICATIONS PATHWAY
#
#                                  +---------- (external libraries) -----------+
#                                  |                                           |
#                                  |                                           |
#                      Browser          Browser            Python Web Server            Python
#                     GUI code         (built-in)         (localhost:<port>/ws)       server code   
#                                                                              
#                   JS WebClient      JS WebSocket         mViewer.mvWSHandler     mViewer functions
#                   ------------      ------------         -------------------     -----------------
#                                                                                 
#   Javascript        send()      ->    send()       ==>    on_message()      ->   from_browser()
#    mViewer   <->                                                                 update_display()
#      GUI          receive()     <-  onmessage()    <==    write_message()   <-   to_browser()
#
#
#                      The Python on_message() and write_message() methods are part of the 
#                      tornado.Application framework but the actual code is written by us.
#                      The associated Javascript send() and onmessage() functions are part  
#                      of the browser built-in WebSocket functionality.  Together they let
#                      us connect messages generated in our Javascript code with our 
#                      back-end Python processing.
#
#---------------------------------------------------------------------------------                                                                                 
                                                                                  
#---------------------------------------------------------------------------------
# MVSTRUCT  This simple class is used to parse return structures
# from the Montage C services.

class mvStruct(object):

  # Text structure parser

    def __init__(self, command, string):

        string = string[8:-1]

        strings = {}
        while True:
            try:
                p1 = string.index('"')
                p2 = string.index('"', p1 + 1)
                substring = string[p1 + 1:p2]
                key = hashlib.md5(substring.encode('ascii')).hexdigest()
                strings[key] = substring
                string = string[:p1] + key + string[p2 + 1:]
            except:
                break

        for pair in string.split(', '):
            key, value = pair.split('=')
            value = value.strip(' ')
            if value in strings:
                self.__dict__[key] = strings[value]
            else:
                self.__dict__[key] = self.simplify(value)


    def simplify(self, value):
        try:
            return int(value)
        except:
            return float(value)


  # Standard object "representation" string

    def __str__(self):

        string = ""
        for item in self.__dict__:
            substr = "%20s" % (item)
            string += substr + " : " + str(self.__dict__[item])+ "\n"
        return string[:-1]


  # Standard object "representation" string

    def __repr__(self):

        thisObj = dir(self)

        string = "{"

        count = 0

        for item in thisObj:

            val = getattr(self, item)

            if item[0:2] == "__": 
                continue

            if item == "simplify": 
                continue

            if val == "": 
                continue

            if count > 0:
                string += ", "

            if isinstance(val, str):
                try:
                    float(val)
                    string += '"' + item + '": ' + str(val)
                except:
                    string += '"' + item + '": "' + str(val) + '"'
            else:
                string += '"' + item + '": ' + repr(val)

            count += 1

        string += "}"

        return string

#---------------------------------------------------------------------------------


#---------------------------------------------------------------------------------
# MVVIEWOVERLAY   Data holder class for overlay information.

# These three classes here are pure data holders to provide 
# structure for an mViewer display.   The main one (mvView) 
# describes the whole display and contains an arbitrary number 
# of mvViewOverlay objects for the overlays on the main image.
# It also contains four mViewer.mvViewFile objects for the gray or 
# red, green, blue file info.

# We also need information on image/canvas sizes and cutout
# offsets in order to map zoom regions and picks to original
# image coordinates and to shrink/expand the displayed region
# to fit the window.

class mvViewOverlay:
    type         =  ""
    visible      = True
    coord_sys    =  ""
    color        =  ""
    data_file    =  ""
    data_col     =  ""
    data_ref     =  ""
    data_type    =  ""
    sym_size     =  ""
    sym_type     =  ""
    sym_sides    =  ""
    sym_rotation =  ""
    lon          =  ""
    lat          =  ""
    text         =  ""
 
        
  # Standard object "string" representation

    def __str__(self):

        thisObj = dir(self)

        string = ""

        for item in thisObj:

            val = getattr(self, item)

            if item[0:2] == "__": 
                continue

            if val == "": 
                continue

            substr = "%40s" % (item)

            if isinstance(val, str):
                string += substr + ": '" + str(val) + "'\n"
            else:
                string += substr + ": " + str(val) + "\n"

        return string


  # Standard object "representation" string

    def __repr__(self):

        thisObj = dir(self)

        string = "{"

        count = 0

        for item in thisObj:

            val = getattr(self, item)

            if item[0:2] == "__": 
                continue

            if val == "": 
                continue

            objType = val.__class__.__name__

            if count > 0:
                string += ", "


            if objType == "bool":

                if val == True:
                    string += '"' + item + '": true'
                elif val == False:
                    string += '"' + item + '": false'

            else:

                if isinstance(val, str):
                    try:
                        float(val)
                        string += '"' + item + '": ' + str(val)
                    except:
                        string += '"' + item + '": "' + str(val) + '"'
                else:
                    string += '"' + item + '": ' + repr(val)

            count += 1

        string += "}"

        return string

#---------------------------------------------------------------------------------


#---------------------------------------------------------------------------------
# MVVIEWFILE  Data holder class for image file information.

class mvViewFile:
    fits_file    = ""
    color_table  = ""
    stretch_min  = ""
    stretch_max  = ""
    stretch_mode = ""
    min          = ""
    max          = ""
    data_min     = ""
    data_max     = ""
    min_sigma    = ""
    max_sigma    = ""
    min_percent  = ""
    max_percent  = ""
    # bunit        = ""


  # Standard object "string" representation

    def __str__(self):

        thisObj = dir(self)

        string = ""

        for item in thisObj:

            val = getattr(self, item)

            if item[0:2] == "__": 
                continue

            if val == "": 
                continue

            substr = "%40s" % (item)

            string += substr + ": '" + str(val) + "'\n"

        return string


  # Standard object "representation" string

    def __repr__(self):

        thisObj = dir(self)

        string = "{"

        count = 0

        for item in thisObj:

            val = getattr(self, item)

            if item[0:2] == "__": 
                continue

            if val == "": 
                continue

            if count > 0:
                string += ", "

            if isinstance(val, str):
                try:
                    float(val)
                    string += '"' + item + '": ' + str(val)
                except:
                    string += '"' + item + '": "' + str(val) + '"'
            else:
                string += '"' + item + '": ' + repr(val)

            count += 1

        string += "}"

        return string

#---------------------------------------------------------------------------------


#---------------------------------------------------------------------------------
# MVVIEW  Data holder class for the whole view.
#
# These are the quantities that we use to populate the update structure every 
# time the image on the screen changes in any way.


class mvView:


  # Default values (to be overridden by actual image information)

    image_file      = "viewer.png"
    image_type      = "png"
    disp_width      = "1000"
    disp_height     = "1000"
    image_width     = "1000"
    image_height    = "1000"

    display_mode    = ""

    cutout_x_offset = ""
    cutout_y_offset = ""
    canvas_height   = 1000
    canvas_width    = 1000
    xmin            = ""
    ymin            = ""
    xmax            = ""
    ymax            = ""
    factor          = ""

    currentPickX = 0
    currentPickY = 0

    current_color           = "black"

    current_symbol_type     = "circle"
    current_symbol_size     =  1.0
    current_symbol_sides    =  3
    current_symbol_rotation =  0.0

    current_coord_sys       = "Equ J2000"

    gray_file  = mvViewFile()
    red_file   = mvViewFile()
    green_file = mvViewFile()
    blue_file  = mvViewFile()

    bunit = "DN"

    overlay = []


  # Standard object "string" representation

    def __str__(self):

        thisObj = dir(self)

        string = "\n"

        count = 0

        for item in thisObj:

            val = getattr(self, item)

            if item[0:2] == "__": 
                continue

            if item == 'json_update':
                continue

            if item == 'update_view':
                continue

            if val == "": 
                continue

            substr = "%25s" % (item)

            objType = val.__class__.__name__

            if objType == 'str':
                string += substr + ": '" + str(val) + "'\n"

            elif objType == 'list':

                string += substr + ":\n"

                count = 0
                for ovly in val:
                   label = "%38s %d:\n" % ("Overlay", count)

                   string += label
                   string += ovly.__str__() 

                   count += 1

            elif objType == 'mvViewFile':

                string += substr + ":\n"

                string += val.__str__() 

            else:
                string += substr + ": " + str(val) + "\n"

            count += 1

        string += "\n"

        return string


  # Standard object "representation" string

    def __repr__(self):

        thisObj = dir(self)

        string = "{"

        count = 0

        for item in thisObj:

            val = getattr(self, item)


            if item[0:2] == "__": 
                continue

            objType = val.__class__.__name__

            if objType == "instancemethod":
                continue

            if objType == "builtin_function_or_method":
                continue

            if val == "": 
                continue

            if count > 0:
                string += ", "

            if isinstance(val, str):
                try:
                    float(val)
                    string += '"' + item + '": ' + str(val)
                except:
                    string += '"' + item + '": "' + str(val) + '"'
            else:
                string += '"' + item + '": ' + repr(val)

            count += 1

        string += "}"

        return string



  # Updates coming from Javascript will be in the form of a JSON string.  
  # This method loads the view with the contents of such.

    def json_update(self, json_str):

        json_dict = json.loads(json_str)

        self.update_view(json_dict, 0, None)
        


  # The above code turns the JSON string into a Python dictionary
  # This routine recursively transfers the values in that dictionary
  # to this mvView object.  We don't yet deal with the possibility
  # of the JSON having different structure from the current object;
  # that would complicate things considerably.  
  #
  # If needed in future iterations of the application, we will
  # deal with updates (e.g. adding an overlay or switching between
  # grayscale and color) via separate commands.

    def update_view(self, parms, index, parents):

        if parents is None:
           parents = []
 
        for key, val in parms.iteritems():
 
            newlist = list(parents)
 
            if len(newlist) > 0:
                newlist.append(index)
 
            newlist.append(str(key))
 
            objType = val.__class__.__name__
 
            if objType == "float" or objType == "int" or objType == "str" or objType == "unicode" or objType == "bool":
 
                newlist.append(str(key))
 
                depth = len(newlist)
 
                depth = depth / 2
 
                element = self
 
                for i in range(0, depth-1):
 
                    name = newlist[2 * i]
                    ind  = newlist[2 * i + 1]
 
                    element = getattr(element, name)
 
                    elementType = element.__class__.__name__
 
                    if elementType == "list":
                        element = element[ind]
 
                print str(key) + " | " + str(val)

                if objType == "unicode":
                    setattr(element, str(key), str(val))
                else:
                    setattr(element, str(key), val)
 
            elif objType == "list":
                 count = 0
                 for list_item in val:
                   self.update_view(list_item, count, newlist)
                   count = count + 1
 
            elif objType == "dict":
                self.update_view(val, 0, newlist)
 
            else:
                print "ERROR> Object in our dictionary?  Should not be possible."

#---------------------------------------------------------------------------------


#---------------------------------------------------------------------------------
# MVMAINHANDLER  Tornado support class for the index.html download.

# This and the next object are used by Tornado as document type handlers 
# for its web server functionality.  This one is for retrieving "index.html";
# the next for processing commands sent from Javascript.  Our tornado instance
# actually uses one more: a built-in method for simple file retrieval (which
# we use to get a bunch of static files like Javascript libraries and banner
# images to the browser.


class mvMainHandler(tornado.web.RequestHandler):

  # This object needs the workspace 

    def initialize(self, data):

        self.data      = data
        self.workspace = self.data['workspace']


  # The initialization GET returns the index.html
  # file we put in the workspace

    def get(self):
    
        loader = tornado.template.Loader(".")

        self.write(loader.load(self.workspace + "/index.html").generate())

#---------------------------------------------------------------------------------


#---------------------------------------------------------------------------------
# MVWSHANDLER  Tornado support class for browser "processing" requests.


class mvWSHandler(tornado.websocket.WebSocketHandler):

  # The methods of this tornado RequestHandler are
  # predefined; we just fill in the functionality we
  # need.  We make use of the intialization method
  # to give the mViewer object a handle to this 
  # webserver (which it needs for sending messages
  # to the browser).

    def initialize(self, data):

        self.debug = False
        
        self.data      = data;
        self.viewer    = self.data['viewer']
        self.view      = self.viewer.view

        self.viewer.webserver = self


  # This is another "pre-defined" tornado method.
  # If the browser sends a message that it is shutting
  # down, we take the oppurtunity to delete the workspace

    def open(self):

        if self.debug:
           print "mvWSHandler.open()"

        self.write_message("mViewer python server connection accepted.")
        self.write_message("")


  # This is where we process "commands" coming
  # from the browser.  These are things like 
  # resize, zoom and pick events.  All we do 
  # in the webserver code is to pass them along
  # to mViewer for processing.

    def on_message(self, message):

        if self.debug:
           print "mvWSHandler.on_message('" + message + "')"

        self.viewer.from_browser(message);


  # If the browser sends a message that it is shutting
  # down, we take the oppurtunity to delete the workspace

    def on_close(self):

        if self.debug:
           print "mvWSHandler.open()"

        print '\nWeb connection closed by browser. Deleting workspace.'

        self.viewer.close()

        sys.stdout.write('\n>>> ')
        sys.stdout.flush()

#---------------------------------------------------------------------------------


#---------------------------------------------------------------------------------
# MVTHREAD  Second thread, for running Tornado web server.

# Since we want to have the web window containing mViewer open 
# while still allowing interactive Python processing, we need 
# to put the Tornado connection in a separate thread.


class mvThread(Thread):
 
    def __init__(self, port, workspace, viewer, view):
        
        Thread.__init__(self)

        self.remote    = None
        self.port      = port
        self.workspace = workspace
        self.view      = view
        self.viewer    = viewer

        self.handler   = mvWSHandler

        self.debug = False

        self.daemon    = True    # If we make the thread a daemon, 
                                 # it closes when the process finishes.
 
    def run(self):

        if self.workspace is None:
            print "Please set a workspace location first."
            return

        data = dict(view=self.view, viewer=self.viewer, port=self.port, workspace=self.workspace)

        application = tornado.web.Application([
            (r'/ws',   mvWSHandler,                   dict(data=data)),
            (r'/',     mvMainHandler,                 dict(data=data)),
            (r"/(.*)", tornado.web.StaticFileHandler, {"path": self.workspace})
        ])


      # Here we would populate the workspace and configure
      # its specific index.html to use this specific port

        application.listen(self.port)

        if self.debug:
            print "DEBUG> mvThread: port = " + str(self.port)

        platform = sys.platform.lower()

        browser = "firefox"

        if platform == 'darwin':
            browser = "safari"
        elif platform.find("win") == 0: 
            browser = "C:/Program\ Files\ (x86)/Mozilla\ Firefox/firefox.exe %s"

        if self.debug:
            print "DEBUG> mvThread: browser = [" + str(browser) + "]"

        webbrowser.get(browser).open("localhost:" + str(self.port))

        tornado.ioloop.IOLoop.instance().start()

#---------------------------------------------------------------------------------


#---------------------------------------------------------------------------------
# MVIEWER  Main entry point.  We name the three "main" parts of the
# system (this Python entry point, the Javascript main entry point,
# and the back-end C image generation utility all "mViewer" to 
# identify them as a set.


class mViewer():

  # Initialization (mostly setting up the workspace)

    def __init__(self, *arg):

        self.debug = True

        nargs = len(arg)

        if nargs == 0:
            workspace = tempfile.mkdtemp(prefix="mvWork_", dir=".")
        else:
            workspace = arg[0]

        workspace = workspace.replace("\\", "/")

        try:
            os.makedirs(workspace)

        except OSError as exception:

            if exception.errno != errno.EEXIST:
                raise
                return

        self.workspace = workspace
        self.view      = mvView()

        self.pick_callback = self.pick_location

        if self.debug:
           print "Workspace: " + self.workspace



  # Use the webserver connection to write commands
  # to the Javascript in the browser.

    def to_browser(self, msg):

        if self.debug:
            print "DEBUG> mViewer.to_browser('" + msg + "')"

        self.webserver.write_message(msg)



  # Shutdown (remove workspace and delete temporary files - subimages, etc.)

    def close(self):

        try:
            files = os.listdir(self.workspace)

            for file in files:
                print self.workspace + "/" + file
                os.remove(self.workspace + "/" + file)
        except:
            print "Workspace cleanup failed."

        try:
            os.rmdir(self.workspace)
        except:
            print "Workspace directory ('" + self.workspace + "') delete failed"

        try:
            self.command("close")

            print "Browser connection closed."

        except:
            print "No active browser connection."

        # Failure or incomplete execution of a close may result in 
        # extraneous temporary files in the work directory, which
        # must be removed manually.


  # Utility function: set the display mode (grayscale / color)

    def set_display_mode(self, mode):

        mode = str(mode)

        if len(mode) == 0:
           mode = "grayscale"

        if mode[0] == 'g':
            self.view.display_mode = "grayscale"

        if mode[0] == 'G':
            self.view.display_mode = "grayscale"

        if mode[0] == 'b':
            self.view.display_mode = "grayscale"

        if mode[0] == 'B':
            self.view.display_mode = "grayscale"

        if mode[0] == 'r':
            self.view.display_mode = "color"

        if mode[0] == 'R':
            self.view.display_mode = "color"

        if mode[0] == 'c':
            self.view.display_mode = "color"

        if mode[0] == 'C':
            self.view.display_mode = "color"

        if mode[0] == 'f':
            self.view.display_mode = "color"

        if mode[0] == 'F':
            self.view.display_mode = "color"


  # Utility function: set the gray_file

    def set_gray_file(self, gray_file):

        self.view.gray_file.fits_file = gray_file

        if self.view.display_mode == "":
            self.view.display_mode = "grayscale"


  # Utility function: set the blue_file

    def set_blue_file(self, blue_file):

        self.view.blue_file.fits_file = blue_file

        if self.view.display_mode == "":
            if self.view.red_file.fits_file != "" and self.view.green_file.fits_file != "":
                self.view.display_mode = "color"


  # Utility function: set the green_file

    def set_green_file(self, green_file):

        self.view.green_file.fits_file = green_file

        if self.view.display_mode == "":
            if self.view.red_file.fits_file != "" and self.view.blue_file.fits_file != "":
                self.view.display_mode = "color"


  # Utility function: set the red_file

    def set_red_file(self, red_file):

        self.view.red_file.fits_file = red_file

        if self.view.display_mode == "":
            if self.view.green_file.fits_file != "" and self.view.blue_file.fits_file != "":
                self.view.display_mode = "color"


  # Utility function: set the current_color

    def set_current_color(self, current_color):

        self.view.current_color = current_color


  # Utility function: set the currentSymbol

    def set_current_symbol(self, *arg):
    
        nargs = len(arg)

        symbol_sides    = ""
        symbol_rotation = ""

        symbol_size     = arg[0]
        symbol_type     = arg[1]

        if nargs > 2:
            symbol_sides = arg[2]

        if nargs > 3:
            symbol_rotation = arg[3]

        self.view.current_symbol_size     = symbol_size
        self.view.current_symbol_type     = symbol_type
        self.view.current_symbol_sides    = symbol_sides
        self.view.current_symbol_rotation = symbol_rotation


  # Utility function: set the coord_sys

    def set_current_coord_sys(self, coord_sys):

        self.view.current_coord_sys = coord_sys


  # Utility function: set the color table (grayscale file)

    def set_color_table(self, color_table):

        self.view.gray_file.color_table = color_table


  # Utility function: set the grayscale color stretch

    def set_gray_stretch(self, stretch_min, stretch_max, stretch_mode):

        self.view.gray_file.stretch_min  = stretch_min
        self.view.gray_file.stretch_max  = stretch_max
        self.view.gray_file.stretch_mode = stretch_mode


  # Utility function: set the blue color stretch

    def set_blue_stretch(self, stretch_min, stretch_max, stretch_mode):

        self.view.blue_file.stretch_min  = stretch_min
        self.view.blue_file.stretch_max  = stretch_max
        self.view.blue_file.stretch_mode = stretch_mode


  # Utility function: set the green color stretch

    def set_green_stretch(self, stretch_min, stretch_max, stretch_mode):

        self.view.green_file.stretch_min  = stretch_min
        self.view.green_file.stretch_max  = stretch_max
        self.view.green_file.stretch_mode = stretch_mode


  # Utility function: set the red color stretch

    def set_red_stretch(self, stretch_min, stretch_max, stretch_mode):

        self.view.red_file.stretch_min  = stretch_min
        self.view.red_file.stretch_max  = stretch_max
        self.view.red_file.stretch_mode = stretch_mode


  # Utility function: add a grid overlay

    def add_grid(self, coord_sys):

        ovly = mvViewOverlay()

        ovly.type     = "grid"
        ovly.visible  =  True
        ovly.color    =  self.view.current_color
        ovly.coord_sys =  coord_sys

        self.view.overlay.append(ovly)

        return ovly


  # Utility function: add a catalog overlay

    def add_catalog(self, data_file, data_col, data_ref, data_type):

        ovly = mvViewOverlay()

        ovly.type         = "catalog"
        ovly.visible      =  True
        ovly.sym_size     =  self.view.current_symbol_size
        ovly.sym_type     =  self.view.current_symbol_type
        ovly.sym_sides    =  self.view.current_symbol_sides
        ovly.sym_rotation =  self.view.current_symbol_rotation
        ovly.coord_sys    =  self.view.current_coord_sys
        ovly.data_file    =  data_file
        ovly.data_col     =  data_col
        ovly.data_ref     =  data_ref
        ovly.data_type    =  data_type 
        ovly.color        =  self.view.current_color

        self.view.overlay.append(ovly)

        return ovly


  # Utility function: add an imginfo overlay

    def add_img_info(self, data_file):

        ovly = mvViewOverlay()

        ovly.type      = "imginfo"
        ovly.visible   = True
        ovly.data_file = data_file
        ovly.color     = self.view.current_color
        ovly.coord_sys = self.view.current_coord_sys

        self.view.overlay.append(ovly)

        return ovly


  # Utility function: add a marker overlay

    def add_marker(self, lon, lat):

        ovly = mvViewOverlay()

        ovly.type         = "mark"
        ovly.visible      =  True
        ovly.sym_size     =  self.view.current_symbol_size
        ovly.sym_type     =  self.view.current_symbol_type
        ovly.sym_sides    =  self.view.current_symbol_sides
        ovly.sym_rotation =  self.view.current_symbol_rotation
        ovly.lon          =  lon
        ovly.lat          =  lat
        ovly.coord_sys    =  self.view.current_coord_sys
        ovly.color        =  self.view.current_color

        self.view.overlay.append(ovly)

        return ovly


  # Utility function: add a label overlay

    def add_label(self, lon, lat, text):

        ovly = mvViewOverlay()

        ovly.type      = "label"
        ovly.visible   =  True
        ovly.lon       =  lon
        ovly.lat       =  lat
        ovly.text      =  text
        ovly.coord_sys =  self.view.current_coord_sys
        ovly.color     =  self.view.current_color

        self.view.overlay.append(ovly)

        return ovly


  # Start a second thread to interact with the browser.

    def init_browser_display(self):

        self.port = random.randint(10000,60000)

        template_file = resource_filename('astroMontage', 'web/index.html')
        index_file    = self.workspace + "/index.html"

        port_string   = str(self.port)

        with open(index_file,'w') as new_file:
           with open(template_file) as old_file:
              for line in old_file:
                 new_file.write(line.replace("\\PORT\\", port_string))


      # Copy all required web files into work directory 
      # (includes Javascript, css, icons, etc.)
      #---------------------------------------------------------------------------
      # JSON files (coordinate "pick" statistic information)
      #---------------------------------------------------------------------------

        in_file  = resource_filename('astroMontage', 'web/pick.json')
        out_file = self.workspace + '/pick.json'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pick0.json')
        out_file = self.workspace + '/pick0.json'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pick1.json')
        out_file = self.workspace + '/pick1.json'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pick2.json')
        out_file = self.workspace + '/pick2.json'
        shutil.copy(in_file, out_file)

      #---------------------------------------------------------------------------
      # CSS files
      #---------------------------------------------------------------------------

        in_file  = resource_filename('astroMontage', 'web/stylesheet01.css')
        out_file = self.workspace + '/stylesheet01.css'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/ColorStretch.css')
        out_file = self.workspace + '/ColorStretch.css'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/LayerControl.css')
        out_file = self.workspace + '/LayerControl.css'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/RegionStats.css')
        out_file = self.workspace + '/RegionStats.css'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/FITSHeaderViewer.css')
        out_file = self.workspace + '/FITSHeaderViewer.css'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/InfoDisplay.css')
        out_file = self.workspace + '/InfoDisplay.css'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/ZoomControl.css')
        out_file = self.workspace + '/ZoomControl.css'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/spectrum.css')
        out_file = self.workspace + '/spectrum.css'
        shutil.copy(in_file, out_file)

      #---------------------------------------------------------------------------
      # Javascript files
      #---------------------------------------------------------------------------

        in_file  = resource_filename('astroMontage', 'web/WebClient.js')
        out_file = self.workspace + '/WebClient.js'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/mViewer.js')
        out_file = self.workspace + '/mViewer.js'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/iceGraphics.js')
        out_file = self.workspace + '/iceGraphics.js'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/ColorStretch.js')
        out_file = self.workspace + '/ColorStretch.js'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/LayerControl.js')
        out_file = self.workspace + '/LayerControl.js'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/RegionStats.js')
        out_file = self.workspace + '/RegionStats.js'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/FITSHeaderViewer.js')
        out_file = self.workspace + '/FITSHeaderViewer.js'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/InfoDisplay.js')
        out_file = self.workspace + '/InfoDisplay.js'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/ZoomControl.js')
        out_file = self.workspace + '/ZoomControl.js'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/spectrum.js')
        out_file = self.workspace + '/spectrum.js'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/viewerUtils.js')
        out_file = self.workspace + '/viewerUtils.js'
        shutil.copy(in_file, out_file)

      #---------------------------------------------------------------------------
      # 30x30 Icons
      #---------------------------------------------------------------------------

        in_file  = resource_filename('astroMontage', 'web/colors.gif')
        out_file = self.workspace + '/colors.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/info.gif')
        out_file = self.workspace + '/info.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/layercontrol.gif')
        out_file = self.workspace + '/layercontrol.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pan_up.gif')
        out_file = self.workspace + '/pan_up.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pan_up_left.gif')
        out_file = self.workspace + '/pan_up_left.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pan_left.gif')
        out_file = self.workspace + '/pan_left.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pan_down_left.gif')
        out_file = self.workspace + '/pan_down_left.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pan_down.gif')
        out_file = self.workspace + '/pan_down.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pan_down_right.gif')
        out_file = self.workspace + '/pan_down_right.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pan_right.gif')
        out_file = self.workspace + '/pan_right.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pan_up_right.gif')
        out_file = self.workspace + '/pan_up_right.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/center_30.gif')
        out_file = self.workspace + '/center_30.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/center_30.png')
        out_file = self.workspace + '/center_30.png'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/regrid.gif')
        out_file = self.workspace + '/regrid.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pick_location.gif')
        out_file = self.workspace + '/pick_location.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/stats.gif')
        out_file = self.workspace + '/stats.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/zoom_in.gif')
        out_file = self.workspace + '/zoom_in.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/zoom_out.gif')
        out_file = self.workspace + '/zoom_out.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/zoom_reset.gif')
        out_file = self.workspace + '/zoom_reset.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/zoom_reset_box.gif')
        out_file = self.workspace + '/zoom_reset_box.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/zoom_pan.gif')
        out_file = self.workspace + '/zoom_pan.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/header_icon.gif')
        out_file = self.workspace + '/header_icon.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/eye02_30.gif')
        out_file = self.workspace + '/eye02_30.gif'
        shutil.copy(in_file, out_file)

      #---------------------------------------------------------------------------
      # 20x20 Icons
      #---------------------------------------------------------------------------

        in_file  = resource_filename('astroMontage', 'web/colors_20.gif')
        out_file = self.workspace + '/colors_20.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/info_20.gif')
        out_file = self.workspace + '/info_20.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/layercontrol_20.gif')
        out_file = self.workspace + '/layercontrol_20.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pan_down_20.gif')
        out_file = self.workspace + '/pan_down_20.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pan_up_20.gif')
        out_file = self.workspace + '/pan_up_20.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pan_left_20.gif')
        out_file = self.workspace + '/pan_left_20.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pan_right_20.gif')
        out_file = self.workspace + '/pan_right_20.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/center_20.png')
        out_file = self.workspace + '/center_20.png'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/image_info_20.gif')
        out_file = self.workspace + '/image_info_20.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/zoom_in_20.gif')
        out_file = self.workspace + '/zoom_in_20.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/zoom_out_20.gif')
        out_file = self.workspace + '/zoom_out_20.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/zoom_reset_20.gif')
        out_file = self.workspace + '/zoom_reset_20.gif'
        shutil.copy(in_file, out_file)

      #---------------------------------------------------------------------------
      # Misc. Icons
      #---------------------------------------------------------------------------

        in_file  = resource_filename('astroMontage', 'web/favicon.ico')
        out_file = self.workspace + '/favicon.ico'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/eye02_22.gif')
        out_file = self.workspace + '/eye02_22.gif'
        shutil.copy(in_file, out_file)




        in_file  = resource_filename('astroMontage', 'web/reload.png')
        out_file = self.workspace + '/reload.png'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/reload_32.png')
        out_file = self.workspace + '/reload_32.png'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/zoom_in_32.png')
        out_file = self.workspace + '/zoom_in_32.png'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/zoom_out_32.png')
        out_file = self.workspace + '/zoom_out_32.png'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/arrow_up_32.png')
        out_file = self.workspace + '/arrow_up_32.png'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/arrow_down_32.png')
        out_file = self.workspace + '/arrow_down_32.png'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/arrow_left_32.png')
        out_file = self.workspace + '/arrow_left_32.png'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/arrow_right_32.png')
        out_file = self.workspace + '/arrow_right_32.png'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/pan.png')
        out_file = self.workspace + '/pan.png'
        shutil.copy(in_file, out_file)

      #---------------------------------------------------------------------------
      # Other image files
      #---------------------------------------------------------------------------

        in_file  = resource_filename('astroMontage', 'web/waitClock.gif')
        out_file = self.workspace + '/waitClock.gif'
        shutil.copy(in_file, out_file)

        in_file  = resource_filename('astroMontage', 'web/galplane_banner.jpg')
        out_file = self.workspace + '/galplane_banner.jpg'
        shutil.copy(in_file, out_file)

      #---------------------------------------------------------------------------


        self.thread = mvThread(self.port, self.workspace, self, self.view)

        self.thread.start()


  # The web browser thread receives any messages the Browser sends
  # These will be commands (like "zoomIn") or requests to process an updated
  # view send as JSON.  That thread forwards the command here.
  #
  # This from_browser() method does any local processing needed to modify
  # the view, then calls the update_display() method to have a new PNG
  # generated and appropriate instructions sent back to the browser.

    def from_browser(self, message):

        if self.debug:
           print "mViewer.from_browser('" + message + "')"


      # Find the image size

        ref_file = self.view.gray_file.fits_file

        if self.view.display_mode == "":
            print "No images defined. Nothing to display."
            sys.stdout.write('\n>>> ')
            sys.stdout.flush()
            return

        if self.view.display_mode == "grayscale":
            ref_file = self.view.gray_file.fits_file

        if self.view.display_mode == "color":
            ref_file = self.view.red_file.fits_file  # R, G, B files should have identical size 

        command = "mExamine " + ref_file

        if self.debug:
           print "\nMONTAGE Command:\n---------------\n" + command

        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stderr = p.stderr.read()

        if stderr:
            print stderr
            raise Exception(stderr)
            return

        retval = mvStruct("mExamine", p.stdout.read().strip())

        if self.debug:
            print "\nRETURN Struct:\n-------------\n"
            print retval
            sys.stdout.write('\n>>> ')
            sys.stdout.flush()

        subimage_width  = retval.naxis1
        subimage_height = retval.naxis2

        if self.view.xmin == "":
            self.view.xmin = 0

        if self.view.xmax == "":
            self.view.xmax = retval.naxis1

        if self.view.ymin == "":
            self.view.ymin = 0

        if self.view.ymax == "":
            self.view.ymax = retval.naxis2

        self.view.image_width  = retval.naxis1
        self.view.image_height = retval.naxis2



      # ------------- Processing commands from the Browser -------------
     
 
      # COMMAND: "update"      
      #
      # Just do/redo the view as it stands
      #-----------------------------------------------------------------

        args = shlex.split(message)

        cmd = args[0]

        if cmd == 'update':
            self.update_display()

      #-----------------------------------------------------------------



      # COMMAND: submitUpdateRequest
      #
      # Received an updated JSON view from the browser.  This is
      # actually the most general request as all sorts of changes
      # might be made to the view on the browser side.  The rest
      # of the commands below are special cases (e.g. "zoomIn")
      # for when it makes more sense to have Python (in conjunction
      # with the Montage executables) figure out what needs to be
      # updated.
      #-----------------------------------------------------------------

        elif cmd == 'submitUpdateRequest':

            jsonStr = args[1]

            self.view.json_update(jsonStr)

            self.update_display()

      #-----------------------------------------------------------------


      # COMMAND: "resize"
      #
      # Resizing the canvas
      #-----------------------------------------------------------------

        elif cmd == 'resize':

            self.view.canvas_width  = args[1]
            self.view.canvas_height = args[2]

            if self.view.factor == 0:

                self.view.xmin = 1
                self.view.xmax = self.view.image_width
                self.view.ymin = 1
                self.view.ymax = self.view.image_height

            self.update_display()

      #-----------------------------------------------------------------


      # COMMAND: "zoomReset"
      #
      # Resetting the zoom
      #-----------------------------------------------------------------

        elif cmd == 'zoomReset':

            self.view.xmin = 1
            self.view.xmax = self.view.image_width
            self.view.ymin = 1
            self.view.ymax = self.view.image_height

            self.update_display()

      #-----------------------------------------------------------------


      # COMMAND: General Zoom/Pan Commands 
      #          "zoom", "zoomIn", "zoomOut", 
      #          "panUp", "panDown", "panLeft", "panRight"
      #
      # There is a lot of common code for zooming and panning, 
      # so we group those commands together

        elif (cmd == 'zoom'        or cmd == 'zoomIn'     or cmd == 'zoomOut' or
              cmd == 'panUp'       or cmd == 'panDown'    or 
              cmd == 'panLeft'     or cmd == 'panRight'   or
              cmd == 'panUpLeft'   or cmd == 'panUpRight' or 
              cmd == 'panDownLeft' or cmd == 'panDownRight'):

            boxxmin = 0.
            boxxmax = float(self.view.canvas_width);
            boxymin = 0.
            boxymax = float(self.view.canvas_height);

            if self.debug:
                print ""
                print ""
                print "ZOOMPAN> cmd: [" + cmd + "]"

                print "ZOOMPAN> Size of currently-diplayed PNG"
                print "ZOOMPAN> " + str(self.view.disp_width) + " X " + str(self.view.disp_height)
                print ""
                print "ZOOMPAN> Canvas:"
                print "ZOOMPAN> " + str(self.view.canvas_width) + " X " + str(self.view.canvas_height)

 
          # We need to know what the current image ranges were

            oldxmin = float(self.view.xmin)
            oldxmax = float(self.view.xmax)
            oldymin = float(self.view.ymin)
            oldymax = float(self.view.ymax)

            if self.debug:
                print ""
                print "ZOOMPAN> Pixel ranges from the previous cutout"
                print "ZOOMPAN> oldx: " + str(oldxmin) + " to " + str(oldxmax)
                print "ZOOMPAN> oldy: " + str(oldymin) + " to " + str(oldymax)
 

            # For box zooming, we are given the box boundaries 
            # but for zoom in/out and panning we need to calculate them 
            # based on the canvas

            if cmd == 'zoom':

                if self.debug:
                    print ""
                    print "ZOOMPAN> Box from command line"

                boxxmin = float(args[1])
                boxxmax = float(args[2])
                boxymin = float(args[3])
                boxymax = float(args[4])


            elif cmd == 'zoomIn':

                if self.debug:
                    print ""
                    print "ZOOMPAN> Box by zooming in"

                box_width  = float(self.view.canvas_width)

                box_center = box_width / 2.

                boxxmin = box_center - box_width / 4.
                boxxmax = box_center + box_width / 4.

                box_height  = float(self.view.canvas_height)

                box_center = box_height / 2.

                boxymin = box_center - box_height / 4.
                boxymax = box_center + box_height / 4.


            elif cmd == 'zoomOut':

                if self.debug:
                    print ""
                    print "ZOOMPAN> Box by zooming out"

                box_width  = float(self.view.canvas_width)
                box_center = box_width / 2.

                boxxmin = box_center - box_width
                boxxmax = box_center + box_width

                box_height = float(self.view.canvas_height)
                box_center = box_height / 2.

                boxymin = box_center - box_height
                boxymax = box_center + box_height


            elif cmd == 'panUp':

                if self.debug:
                    print ""
                    print "ZOOMPAN> Box by panning up"

                box_height = float(self.view.canvas_height)

                boxymin = boxymin + box_height / 4.
                boxymax = boxymax + box_height / 4.


            elif cmd == 'panDown':

                if self.debug:
                    print ""
                    print "ZOOMPAN> Box by panning down"

                box_height = float(self.view.canvas_height)

                boxymin = boxymin - box_height / 4.
                boxymax = boxymax - box_height / 4.


            elif cmd == 'panLeft':

                if self.debug:
                    print ""
                    print "ZOOMPAN> Box by panning left"

                box_width = float(self.view.canvas_width)

                boxxmin = boxxmin - box_width / 4.
                boxxmax = boxxmax - box_width / 4.


            elif cmd == 'panRight':

                if self.debug:
                    print ""
                    print "ZOOMPAN> Box by panning right"

                box_width = float(self.view.canvas_width)

                boxxmin = boxxmin + box_width / 4.
                boxxmax = boxxmax + box_width / 4.


            elif cmd == 'panUpLeft':

                if self.debug:
                    print ""
                    print "ZOOMPAN> Box by panning up and left"

                box_height = float(self.view.canvas_height)
                box_width = float(self.view.canvas_width)

                boxymin = boxymin + box_height / (4. * math.sqrt(2))
                boxymax = boxymax + box_height / (4. * math.sqrt(2))
                boxxmin = boxxmin - box_width  / (4. * math.sqrt(2))
                boxxmax = boxxmax - box_width  / (4. * math.sqrt(2))


            elif cmd == 'panUpRight':

                if self.debug:
                    print ""
                    print "ZOOMPAN> Box by panning up and right"

                box_height = float(self.view.canvas_height)
                box_width = float(self.view.canvas_width)

                boxymin = boxymin + box_height / (4. * math.sqrt(2))
                boxymax = boxymax + box_height / (4. * math.sqrt(2))
                boxxmin = boxxmin + box_width  / (4. * math.sqrt(2))
                boxxmax = boxxmax + box_width  / (4. * math.sqrt(2))


            elif cmd == 'panDownLeft':

                if self.debug:
                    print ""
                    print "ZOOMPAN> Box by panning down and left"

                box_height = float(self.view.canvas_height)
                box_width = float(self.view.canvas_width)

                boxymin = boxymin - box_height / (4. * math.sqrt(2))
                boxymax = boxymax - box_height / (4. * math.sqrt(2))
                boxxmin = boxxmin - box_width  / (4. * math.sqrt(2))
                boxxmax = boxxmax - box_width  / (4. * math.sqrt(2))


            elif cmd == 'panDownRight':

                if self.debug:
                    print ""
                    print "ZOOMPAN> Box by panning down and right"

                box_height = float(self.view.canvas_height)
                box_width = float(self.view.canvas_width)

                boxymin = boxymin - box_height / (4. * math.sqrt(2))
                boxymax = boxymax - box_height / (4. * math.sqrt(2))
                boxxmin = boxxmin + box_width  / (4. * math.sqrt(2))
                boxxmax = boxxmax + box_width  / (4. * math.sqrt(2))


            # The box (especially for draw box zooming) will
            # not have the proportions of the canvas.  Correct 
            # that here.

            box_width  = boxxmax-boxxmin
            box_height = boxymax-boxymin

            if self.debug:
                print ""
                print "ZOOMPAN> Input:"
                print "ZOOMPAN> boxx: " + str(boxxmin) + " to " + str(boxxmax) + " [" + str(box_width)  + "]"
                print "ZOOMPAN> boxy: " + str(boxymin) + " to " + str(boxymax) + " [" + str(box_height) + "]"

            box_aspect    = float(box_height)              / float(box_width)
            canvas_aspect = float(self.view.canvas_height) / float(self.view.canvas_width)

            if self.debug:
                print ""
                print "ZOOMPAN> Aspect:"
                print "ZOOMPAN> box:    " + str(box_aspect) 
                print "ZOOMPAN> canvas: " + str(canvas_aspect)


            # Based on the ratio of box aspect ratio to canvas,
            # if the box is taller and skinner than the canvas;
            # make it wider.

            ratio = box_aspect / canvas_aspect

            if self.debug:
                print ""
                print "ZOOMPAN> Apect ratio adjusment factor: " + str(ratio)

            if ratio > 1.:

                box_width = int(box_width * ratio)

                box_center = (boxxmax + boxxmin) / 2.
 
                boxxmin = box_center - box_width / 2.
                boxxmax = box_center + box_width / 2.


            # The box is shorter and fatter than the canvas;
            # make it taller.

            else:

                box_height = int(box_height / ratio)

                box_center = (boxymax + boxymin) / 2.
 
                boxymin = box_center - box_height / 2.
                boxymax = box_center + box_height / 2.


            box_width  = boxxmax-boxxmin
            box_height = boxymax-boxymin

            box_aspect = float(box_height) / float(box_width)

            if self.debug:
                print ""
                print "ZOOMPAN> Adjust to canvas aspect:"
                print "ZOOMPAN> boxx: " + str(boxxmin) + " to " + str(boxxmax) + " [" + str(box_width)  + "]"
                print "ZOOMPAN> boxy: " + str(boxymin) + " to " + str(boxymax) + " [" + str(box_height) + "]"


            # If we are zoomed out far enough that we see the whole image,
            # part of the canvas may not be covered due to a difference in the
            # image and canvas aspect ratios.  In this case (and when zooming
            # part of the zoom box may be off the image.  If we detect this,
            # we shift the zoom box to be as much on the image as possible,
            # with the same sizing.

            if cmd == 'zoom' or cmd == 'zoomIn':
            
                if boxxmax > self.view.disp_width:

                    diff = boxxmax - self.view.disp_width

                    boxxmax = boxxmax - diff
                    boxxmin = boxxmin - diff

                if boxxmin < 0:

                    diff = boxxmin

                    boxxmin = boxxmin - diff
                    boxxmax = boxxmax - diff

                if boxymax > self.view.disp_height:

                    diff = boxymax - self.view.disp_height

                    boxymax = boxymax - diff
                    boxymin = boxymin - diff

                if boxymin < 0:

                    diff = boxymin

                    boxymin = boxymin - diff
                    boxymax = boxymax - diff

                if self.debug:
                    print ""
                    print "ZOOMPAN> After shifting:"
                    print "ZOOMPAN> boxx: " + str(boxxmin) + " to " + str(boxxmax) 
                    print "ZOOMPAN> boxy: " + str(boxymin) + " to " + str(boxymax) 


            # Convert the box back to image coordinates

            factor = float(self.view.factor)

            boxxmin = boxxmin * factor
            boxxmax = boxxmax * factor
            boxymin = boxymin * factor
            boxymax = boxymax * factor

            boxxmin = boxxmin + oldxmin
            boxxmax = boxxmax + oldxmin
            boxymin = boxymin + oldymin
            boxymax = boxymax + oldymin

            if self.debug:
                print ""
                print "ZOOMPAN> In image pixel coordinates:"
                print "ZOOMPAN> boxx: " + str(boxxmin) + " to " + str(oldxmax) 
                print "ZOOMPAN> boxy: " + str(boxymin) + " to " + str(oldymax) 


            if boxxmin < 0:
                boxxmax = boxxmax - boxxmin
                boxxmin = 0

            if boxxmax > self.view.image_width:
                boxxmax = self.view.image_width
                boxxmin = boxxmax - box_width*factor

            if boxymin < 0:
                boxymax = boxymax - boxymin
                boxymin = 0

            if boxymax > self.view.image_height:
                boxymax = self.view.image_height
                boxymin = boxxmax - box_height*factor

            if self.debug:
                print ""
                print "ZOOMPAN> Clipped by the image dimensions:"
                print "ZOOMPAN> boxx: " + str(boxxmin) + " to " + str(oldxmax) 
                print "ZOOMPAN> boxy: " + str(boxymin) + " to " + str(oldymax) 


            # Save them away

            self.view.xmin = int(boxxmin)
            self.view.xmax = int(boxxmax)
            self.view.ymin = int(boxymin)
            self.view.ymax = int(boxymax)

            self.update_display()



        # COMMAND: "center"
        #
        # Shift to the center of the image

        elif cmd == "center":

            # We need to know what the current image ranges were

            oldxmin = float(self.view.xmin)
            oldxmax = float(self.view.xmax)
            oldymin = float(self.view.ymin)
            oldymax = float(self.view.ymax)

            box_width   = float(self.view.canvas_width)
            box_height  = float(self.view.canvas_height)

            # box_xcenter = box_width  / 2.
            # box_ycenter = box_height / 2.

            factor = float(self.view.factor)

            if cmd == 'center':

                # check current pick coordinates are not zero

                if (self.view.currentPickX != 0) and (self.view.currentPickY != 0):
                    boxymax = self.view.currentPickY + ((box_height * factor)/2)
                    boxymin = self.view.currentPickY - ((box_height * factor)/2)
                    boxxmax = self.view.currentPickX + ((box_width * factor)/2)
                    boxxmin = self.view.currentPickX - ((box_width * factor)/2)
                else:
                    boxymax = (self.view.image_height + box_height * factor) / 2
                    boxymin = (self.view.image_height - box_height * factor) / 2
                    boxxmax = (self.view.image_width + box_width  * factor)  / 2
                    boxxmin = (self.view.image_width - box_width  * factor)  / 2

            self.view.xmin = int(boxxmin)
            self.view.xmax = int(boxxmax)
            self.view.ymin = int(boxymin)
            self.view.ymax = int(boxymax)

            self.update_display()


        # COMMAND: "pick"
        #
        # Examine a user-selected location

        elif cmd == 'pick':

            factor = float(self.view.factor)

            boxx = float(args[1])
            boxy = float(args[2])

            self.view.currentPickX = self.view.xmin + boxx * factor
            self.view.currentPickY = self.view.ymin + boxy * factor

            self.pick_location(boxx, boxy)

            # self.update_display()

        # COMMAND: "header"
        #
        # Get FITS header

        elif cmd == 'header':

            self.get_header()


    def update_display(self):

        sys.stdout.write('\n>>> ')
        sys.stdout.flush()
        
        if self.view.display_mode == "":
            print "No images defined. Nothing to display."
            sys.stdout.write('\n>>> ')
            sys.stdout.flush()
            return

        if self.view.display_mode == "grayscale":

            # First cut out the part of the original grayscale image we want

            command = "mSubimage -p" 
            command += " " + self.view.gray_file.fits_file 
            command += " " + self.workspace + "/subimage.fits" 
            command += " " + str(self.view.xmin)
            command += " " + str(self.view.ymin)
            command += " " + str(int(self.view.xmax) - int(self.view.xmin))
            command += " " + str(int(self.view.ymax) - int(self.view.ymin))

            if self.debug:
               print "\nMONTAGE Command:\n---------------\n" + command

            p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stderr = p.stderr.read()

            if stderr:
                raise Exception(stderr)
                return

            retval = mvStruct("mSubimage", p.stdout.read().strip())

            if self.debug:
                print "\nRETURN Struct:\n-------------\n"
                print retval
                sys.stdout.write('\n>>> ')
                sys.stdout.flush()



        else:

            # Or if in color mode, cut out the three images

            # Blue

            command = "mSubimage -p" 
            command += " " + self.view.blue_file.fits_file 
            command += " " + self.workspace + "/blue_subimage.fits" 
            command += " " + str(self.view.xmin)
            command += " " + str(self.view.ymin)
            command += " " + str(int(self.view.xmax) - int(self.view.xmin))
            command += " " + str(int(self.view.ymax) - int(self.view.ymin))

            if self.debug:
               print "\nMONTAGE Command:\n---------------\n" + command

            p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stderr = p.stderr.read()

            if stderr:
                raise Exception(stderr)
                return

            retval = mvStruct("mSubimage", p.stdout.read().strip())

            if self.debug:
                print "\nRETURN Struct:\n-------------\n"
                print retval


            # Green

            command = "mSubimage -p" 
            command += " " + self.view.green_file.fits_file 
            command += " " + self.workspace + "/green_subimage.fits" 
            command += " " + str(self.view.xmin)
            command += " " + str(self.view.ymin)
            command += " " + str(int(self.view.xmax) - int(self.view.xmin))
            command += " " + str(int(self.view.ymax) - int(self.view.ymin))

            if self.debug:
               print "\nMONTAGE Command:\n---------------\n" + command

            p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stderr = p.stderr.read()

            if stderr:
                raise Exception(stderr)
                return

            retval = mvStruct("mSubimage", p.stdout.read().strip())

            if self.debug:
                print "\nRETURN Struct:\n-------------\n"
                print retval


            # Red

            command = "mSubimage -p" 
            command += " " + self.view.red_file.fits_file 
            command += " " + self.workspace + "/red_subimage.fits" 
            command += " " + str(self.view.xmin)
            command += " " + str(self.view.ymin)
            command += " " + str(int(self.view.xmax) - int(self.view.xmin))
            command += " " + str(int(self.view.ymax) - int(self.view.ymin))

            if self.debug:
               print "\nMONTAGE Command:\n---------------\n" + command

            p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stderr = p.stderr.read()

            if stderr:
                raise Exception(stderr)
                return

            retval = mvStruct("mSubimage", p.stdout.read().strip())

            if self.debug:
                print "\nRETURN Struct:\n-------------\n"
                print retval
                sys.stdout.write('\n>>> ')
                sys.stdout.flush()


        # Get the size (all three are the same)

        if self.view.display_mode == "grayscale":
            command = "mExamine " + self.workspace + "/subimage.fits"
        else:
            command = "mExamine " + self.workspace + "/red_subimage.fits"

        if self.debug:
           print "\nMONTAGE Command:\n---------------\n" + command

        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stderr = p.stderr.read()

        if stderr:
            raise Exception(stderr)
            return

        retval = mvStruct("mExamine", p.stdout.read().strip())

        if self.debug:
            print "\nRETURN Struct:\n-------------\n"
            print retval
            sys.stdout.write('\n>>> ')
            sys.stdout.flush()

        subimage_width  = retval.naxis1
        subimage_height = retval.naxis2



        xfactor = float(subimage_width)  / float(self.view.canvas_width)
        yfactor = float(subimage_height) / float(self.view.canvas_height)

        if float(yfactor) > float(xfactor):
            xfactor = yfactor

        self.view.factor = xfactor


        if self.view.display_mode == "grayscale":

            # Shrink/expand the grayscale cutout to the right size

            xfactor = float(subimage_width)  / float(self.view.canvas_width)
            yfactor = float(subimage_height) / float(self.view.canvas_height)

            if float(yfactor) > float(xfactor):
                xfactor = yfactor

            self.view.factor = xfactor

            command = "mShrink" 
            command += " " + self.workspace + "/subimage.fits" 
            command += " " + self.workspace + "/shrunken.fits" 
            command += " " + str(xfactor)

            if self.debug:
               print "\nMONTAGE Command:\n---------------\n" + command

            p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stderr = p.stderr.read()

            if stderr:
                raise Exception(stderr)
                return

            retval = mvStruct("mShrink", p.stdout.read().strip())

            if self.debug:
                print "\nRETURN Struct:\n-------------\n"
                print retval
                sys.stdout.write('\n>>> ')
                sys.stdout.flush()


        else:

            # Shrink/expand the three color cutouts to the right size

            # Blue

            command = "mShrink" 
            command += " " + self.workspace + "/blue_subimage.fits" 
            command += " " + self.workspace + "/blue_shrunken.fits" 
            command += " " + str(xfactor)

            if self.debug:
               print "\nMONTAGE Command:\n---------------\n" + command

            p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stderr = p.stderr.read()

            if stderr:
                raise Exception(stderr)
                return

            retval = mvStruct("mShrink", p.stdout.read().strip())

            if self.debug:
                print "\nRETURN Struct:\n-------------\n"
                print retval


            # Green

            command = "mShrink" 
            command += " " + self.workspace + "/green_subimage.fits" 
            command += " " + self.workspace + "/green_shrunken.fits" 
            command += " " + str(xfactor)

            if self.debug:
               print "\nMONTAGE Command:\n---------------\n" + command

            p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stderr = p.stderr.read()

            if stderr:
                raise Exception(stderr)
                return

            retval = mvStruct("mShrink", p.stdout.read().strip())

            if self.debug:
                print "\nRETURN Struct:\n-------------\n"
                print retval


            # Red

            command = "mShrink" 
            command += " " + self.workspace + "/red_subimage.fits" 
            command += " " + self.workspace + "/red_shrunken.fits" 
            command += " " + str(xfactor)

            if self.debug:
               print "\nMONTAGE Command:\n---------------\n" + command

            p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stderr = p.stderr.read()

            if stderr:
                raise Exception(stderr)
                return

            retval = mvStruct("mShrink", p.stdout.read().strip())

            if self.debug:
                print "\nRETURN Struct:\n-------------\n"
                print retval
                sys.stdout.write('\n>>> ')
                sys.stdout.flush()



        # Finally, generate the JPEG

        command = "mViewer"

        noverlay = len(self.view.overlay)

        for i in range(0, noverlay):

            type = self.view.overlay[i].type

            if   type == 'grid':

                visible  = self.view.overlay[i].visible
                coord_sys = self.view.overlay[i].coord_sys
                color    = self.view.overlay[i].color

                if visible == True:

                    if color != "":
                        command += " -color " + str(color)

                    command += " -grid "  + str(coord_sys)


            elif type == 'catalog':

                visible      = self.view.overlay[i].visible
                data_file    = self.view.overlay[i].data_file
                data_col     = self.view.overlay[i].data_col
                data_ref     = self.view.overlay[i].data_ref
                data_type    = self.view.overlay[i].data_type
                sym_size     = self.view.overlay[i].sym_size
                sym_type     = self.view.overlay[i].sym_type
                sym_sides    = self.view.overlay[i].sym_sides
                sym_rotation = self.view.overlay[i].sym_rotation
                color        = self.view.overlay[i].color

                if visible == True:

                    if color != "":
                        command += " -color " + str(color)

                    if sym_type != "" and sym_size != "":
                        command += " -symbol " + str(sym_size) + " " + str(sym_type) + " " + str(sym_sides) + " " + str(sym_rotation)

                    command += " -catalog "  + str(data_file) + " " + str(data_col) + " " + str(data_ref) + " " + str(data_type)


            elif type == 'imginfo':

                visible   = self.view.overlay[i].visible
                data_file = self.view.overlay[i].data_file
                color     = self.view.overlay[i].color

                if visible == True:

                    if color != "":
                        command += " -color " + str(color)

                    command += " -imginfo "  + str(data_file)


            elif type == 'mark':

                visible      = self.view.overlay[i].visible
                lon          = self.view.overlay[i].lon
                lat          = self.view.overlay[i].lat
                sym_size     = self.view.overlay[i].sym_size
                sym_type     = self.view.overlay[i].sym_type
                sym_sides    = self.view.overlay[i].sym_sides
                sym_rotation = self.view.overlay[i].sym_rotation
                color        = self.view.overlay[i].color

                if visible == True:

                    if color != "":
                        command += " -color " + str(color)

                    if sym_type != "" and sym_size != "":
                        command += " -symbol " + str(sym_size) + " " + str(sym_type) + " " + str(sym_sides) + " " + str(sym_rotation)

                    command += " -mark "  + str(lon) + " " + str(lat)


            elif type == 'label':

                visible  = self.view.overlay[i].visible
                lon      = self.view.overlay[i].lon
                lat      = self.view.overlay[i].lat
                text     = self.view.overlay[i].text
                color    = self.view.overlay[i].color

                if visible == True:

                    if color != "":
                        command += " -color " + str(color)

                    command += " -label "  + str(lon) + " " + str(lat) + ' "' + str(text) + '"'


            else:
                print "Invalid overlay type '" + str(type) + "' in view specification."


        if self.view.display_mode == "grayscale":

            fits_file    = self.workspace + "/shrunken.fits"
            color_table  = self.view.gray_file.color_table
            stretch_min  = self.view.gray_file.stretch_min
            stretch_max  = self.view.gray_file.stretch_max
            stretch_mode = self.view.gray_file.stretch_mode

            if color_table == "":
               color_table = 0

            if stretch_min == "":
               stretch_min = "-1s"

            if stretch_max == "":
               stretch_max = "max"

            if stretch_mode == "":
               stretch_mode = "gaussian-log"

            command += " -ct " + str(color_table)
            command += " -gray " + str(fits_file) + " " + str(stretch_min) + " " + str(stretch_max) + " " + str(stretch_mode)


        else:

            fits_file    = self.workspace + "/red_shrunken.fits"
            stretch_min  = self.view.red_file.stretch_min
            stretch_max  = self.view.red_file.stretch_max
            stretch_mode = self.view.red_file.stretch_mode
 
            if stretch_min == "":
               stretch_min = "-1s"

            if stretch_max == "":
               stretch_max = "max"

            if stretch_mode == "":
               stretch_mode = "gaussian-log"

            command += " -red " + str(fits_file) + " " + str(stretch_min) + " " + str(stretch_max) + " " + str(stretch_mode)
 
            fits_file    = self.workspace + "/green_shrunken.fits"
            stretch_min  = self.view.green_file.stretch_min
            stretch_max  = self.view.green_file.stretch_max
            stretch_mode = self.view.green_file.stretch_mode
 
            if stretch_min == "":
               stretch_min = "-1s"

            if stretch_max == "":
               stretch_max = "max"

            if stretch_mode == "":
               stretch_mode = "gaussian-log"

            command += " -green " + str(fits_file) + " " + str(stretch_min) + " " + str(stretch_max) + " " + str(stretch_mode)
 
            fits_file    = self.workspace + "/blue_shrunken.fits"
            stretch_min  = self.view.blue_file.stretch_min
            stretch_max  = self.view.blue_file.stretch_max
            stretch_mode = self.view.blue_file.stretch_mode

            if stretch_min == "":
               stretch_min = "-1s"

            if stretch_max == "":
               stretch_max = "max"

            if stretch_mode == "":
               stretch_mode = "gaussian-log"

            command += " -blue " + str(fits_file) + " " + str(stretch_min) + " " + str(stretch_max) + " " + str(stretch_mode)


        image_file = self.view.image_file

        command += " -png " + self.workspace + "/" + str(image_file) 

        if self.debug:
           print "\nMONTAGE Command:\n---------------\n" + command

        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stderr = p.stderr.read()

        if stderr:
            raise Exception(stderr)
            return

        retval = mvStruct("mViewer", p.stdout.read().strip())

        if self.debug:
            print "\nRETURN Struct:\n-------------\n"
            print retval
            sys.stdout.write('\n>>> ')
            sys.stdout.flush()

        if stderr:
            raise Exception(stderr)
            return

        if retval.stat == "WARNING":
            print "\nWARNING: " + retval.msg
            sys.stdout.write('\n>>> ')
            sys.stdout.flush()
            return

        if retval.stat == "ERROR":
            print "\nERROR: " + retval.msg
            sys.stdout.write('\n>>> ')
            sys.stdout.flush()
            return

        self.view.disp_width  = retval.width
        self.view.disp_height = retval.height

        if self.view.display_mode == "grayscale":

			# self.view.gray_file.bunit        = retval.bunit
			self.view.gray_file.min          = retval.min
			self.view.gray_file.max          = retval.max
			self.view.gray_file.data_min     = retval.datamin
			self.view.gray_file.data_max     = retval.datamax
			self.view.gray_file.min_sigma    = retval.minsigma
			self.view.gray_file.max_sigma    = retval.maxsigma 
			self.view.gray_file.min_percent  = retval.minpercent
			self.view.gray_file.max_percent  = retval.maxpercent

        else:

			# self.view.blue_file.bunit        = retval.bunit
			self.view.blue_file.min          = retval.bmin
			self.view.blue_file.max          = retval.bmax
			self.view.blue_file.data_min     = retval.bdatamin
			self.view.blue_file.data_max     = retval.bdatamax
			self.view.blue_file.min_sigma    = retval.bminsigma
			self.view.blue_file.max_sigma    = retval.bmaxsigma 
			self.view.blue_file.min_percent  = retval.bminpercent
			self.view.blue_file.max_percent  = retval.bmaxpercent

			# self.view.green_file.bunit       = retval.bunit
			self.view.green_file.min         = retval.gmin
			self.view.green_file.max         = retval.gmax
			self.view.green_file.data_min    = retval.gdatamin
			self.view.green_file.data_max    = retval.gdatamax
			self.view.green_file.min_sigma   = retval.gminsigma
			self.view.green_file.max_sigma   = retval.gmaxsigma 
			self.view.green_file.min_percent = retval.gminpercent
			self.view.green_file.max_percent = retval.gmaxpercent

			# self.view.red_file.bunit         = retval.bunit
			self.view.red_file.min           = retval.rmin
			self.view.red_file.max           = retval.rmax
			self.view.red_file.data_min      = retval.rdatamin
			self.view.red_file.data_max      = retval.rdatamax
			self.view.red_file.min_sigma     = retval.rminsigma
			self.view.red_file.max_sigma     = retval.rmaxsigma 
			self.view.red_file.min_percent   = retval.rminpercent
			self.view.red_file.max_percent   = retval.rmaxpercent

        self.view.bunit = retval.bunit


        # Write the current mvView info to a JSON file in the workspace

        json_file = self.workspace + "/view.json"

        jfile = open(json_file, "w+")

        jfile.write(repr(self.view))

        jfile.close()


        # Tell the browser to get the new images (and JSON)

        self.to_browser("image " + image_file)




    # Default function to be used when the user picks a location
    # This can be overridden by the developer with a callback of 
    # their own.

    def pick_location(self, boxx, boxy):

        ref_file = []

        if self.view.display_mode == "grayscale":

            ref_file.append(self.view.gray_file.fits_file)


        if self.view.display_mode == "color":

            ref_file.append(self.view.blue_file.fits_file)
            ref_file.append(self.view.green_file.fits_file)
            ref_file.append(self.view.red_file.fits_file)

        radius = 31

        json_file = self.workspace + "/pick.json"
        jfile = open(json_file, "w+")
        jfile.write("[")

        nfile = len(ref_file)

        for i in range(0, nfile):
            command = "mExamine -p " + repr(boxx) + "p " + repr(boxy) + "p " + repr(radius) + "p " + ref_file[i]

            if self.debug:
                print "\nMONTAGE Command:\n---------------\n" + command

            p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stderr = p.stderr.read()

            if stderr:
                raise Exception(stderr)
                return

            retval = mvStruct("mExamine", p.stdout.read().strip())

            if self.debug:
                print "\nRETURN Struct:\n-------------\n"
                print retval
                sys.stdout.write('\n>>> ')
                sys.stdout.flush()

            
            print ""
            print "   File " + ref_file[i] + ":"
            print ""
            print "                 Flux    (sigma)                 (RA, Dec)         Pix Coord"
            print "                ------------------      -------------------------  ----------"
            print "      Center:   " + repr(retval.fluxref) + " (" + repr(retval.sigmaref) + ")  at  (" + repr(retval.raref) + ", " + repr(retval.decref) + ")  [" + repr(retval.xref) + ", " + repr(retval.yref) + "]"
            print "      Min:      " + repr(retval.fluxmin) + " (" + repr(retval.sigmamin) + ")  at  (" + repr(retval.ramin) + ", " + repr(retval.decmin) + ")  [" + repr(retval.xmin) + ", " + repr(retval.ymin) + "]"
            print "      Max:      " + repr(retval.fluxmax) + " (" + repr(retval.sigmamax) + ")  at  (" + repr(retval.ramax) + ", " + repr(retval.decmax) + ")  [" + repr(retval.xmax) + ", " + repr(retval.ymax) + "]"
            print ""
            print "      Average:  " + repr(retval.aveflux) + " +/- " + repr(retval.rmsflux)
            print ""
            print "      Radius:   " + repr(retval.radius) + " degrees (" + repr(retval.radpix) + " pixels) / Total area: " + repr(retval.npixel) + " pixels (" + repr(retval.nnull) + " nulls)"
            print ""


            # Write the current mvView info to a JSON file in the workspace

            # json_file = self.workspace + "/pick" + str(i) + ".json"

            # jfile = open(json_file, "w+")

            jfile.write(repr(retval))

            if i < (nfile-1):
                jfile.write(",")

            print repr(retval)


        jfile.write("]")
        jfile.close()
        self.to_browser("pick")

        sys.stdout.write('\n>>> ')
        sys.stdout.flush()


    def get_header(self):

        ref_file = []

        if self.view.display_mode == "grayscale":

            ref_file.append(self.view.gray_file.fits_file)


        if self.view.display_mode == "color":

            ref_file.append(self.view.blue_file.fits_file)
            ref_file.append(self.view.green_file.fits_file)
            ref_file.append(self.view.red_file.fits_file)


        nfile = len(ref_file)

        for i in range(0, nfile):
            command = "mGetHdr -H " + ref_file[i] + " " + self.workspace + "/header" + str(i) + ".html"

            if self.debug:
                print "\nMONTAGE Command:\n---------------\n" + command

            p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stderr = p.stderr.read()

            if stderr:
                raise Exception(stderr)
                return

            retval = mvStruct("mGetHdr", p.stdout.read().strip())

            if self.debug:
                print "\nRETURN Struct:\n-------------\n"
                print retval
                sys.stdout.write('\n>>> ')
                sys.stdout.flush()

            if self.view.display_mode == "color":
                self.to_browser("header color")
            else:
                self.to_browser("header gray")


        sys.stdout.write('\n>>> ')
        sys.stdout.flush()



    # Send a display update notification to the browser.

    def draw(self):

        if self.debug:
            print "DEBUG> mViewer.draw(): sending 'updateDisplay' to browser."

        self.to_browser("updateDisplay")

#---------------------------------------------------------------------------------
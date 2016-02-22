Montage Viewer (Python mViewer)
===============================

Montage is a large package used by the research community for 
manipulating astronomical images.  One of it's modules generates
(static) PNG/JPEG renderings of this data and there is a basic
Python wrapper aimed at using this capability interactively from
Python.

This work is an extension of that wrapper, providing much more
control of the displayed data and interactive capabilities.  Built
in collaboration with the Montage Project at Caltech, it is a 
drop-in for their package, extending their original code with a
parallel alternate version of their python/Javascript code under
a different name.

Python mViewer uses Montage (C executables/library) for the back-end
processing, Python for command-control (with the ability to insert
additional user-defined processing at will), and a Browser window
(with Javascript controls) for interactive display.  Both the Montage
processing and the browser are controlled from Python.

From the Montage repository docs (https://github.com/Caltech-IPAC/Montage):

Montage (http://montage.ipac.caltech.edu) is an Open Source toolkit,
distributed with a BSD 3-clause license, for assembling Flexible
Image Transport System (FITS) images into mosaics, according to
the user's custom specifications of coordinates, WCS projection,
spatial sampling and rotation. The toolkit contains utilities for
reprojecting and background matching images, assembling them into
mosaics, visualizing the results, and discovering, analyzing and
understanding image metadata from archives or the user's images.
Montage is written in ANSI-C and is portable across all common
*nix platforms, including Linux, Solaris, Mac OSX and Cygwin on
Windows. The distribution contains all libraries needed to build the
toolkit from a single simple "make" command, including the CFITSIO
library and WCS tools. The toolkit is in wide use in astronomy to
support research projects, and to support pipeline development,
product generation and image visualization for major projects and
missions. Montage is used as an exemplar application by the computer
science community in developing next-generation cyberinfrastructure,
especially workflow framework on distributed platforms.

/**************************************************************/
/*  FITS Header Viewer                                        */
/*                                                            */
/*  This is the Javascript for the dialog that displays       */ 
/*  FITS header information about the image(s) being viewed.  */
/*  Elements in this dialog are not manipulated by the user.  */
/**************************************************************/

function FITSHeaderViewer(fitsDivName, viewer)
{
    var me = this;

    me.fitsDivName = fitsDivName;

    me.fitsDiv = document.getElementById(me.fitsDivName);

    me.viewer = viewer;

    me.workspace;
    me.fitsFile;

    me.mode  = "color";
    me.plane = "blue";


//  All FITS headers are loaded into the appropriate divs.  
//  Initially, all are hidden; depending on the display
//  mode and the selected color plane (in the case of 
//  color images), one div is made visible at any given
//  time

    me.init = function()
    {     
        console.log("DEBUG> FitsHeaderDisplay.init()");

        me.mode = viewer.updateJSON.display_mode;
               
        console.log("DEBUG> mode = " + me.mode);

        me.makeControl();

        jQuery("#fitsPlane" ).hide();
        jQuery("#grayHdr"   ).hide();
        jQuery("#blueHdr"   ).hide();
        jQuery("#greenHdr"  ).hide();
        jQuery("#redHdr"    ).hide();

        if(me.mode == "color")
        {
            jQuery("#fitsPlane" ).show();
            jQuery("#blueHdr"   ).show();
        }
        else if(me.mode == "grayscale")
        {
            jQuery("#grayHdr"   ).show();
        }
        else
        {
            console.log("Bad Header Directive: " + me.mode);
        }

        me.viewer.addUpdateCallback(me.processUpdate);
    }


//  Process update (i.e. user selects a new color plane)

    me.processUpdate = function()
    {
        console.log("DEBUG> FitsHeaderDisplay.processUpdate()");

        if(me.plane == "blue")
        {
            jQuery("#blueHdr"   ).show();
            jQuery("#greenHdr"  ).hide();
           jQuery("#redHdr"    ).hide();
        }
        else if(me.plane == "green")
        {
            jQuery("#blueHdr"   ).hide();
            jQuery("#greenHdr"  ).show();
            jQuery("#redHdr"    ).hide();
        }
        else if(me.plane == "red")
        {
            jQuery("#blueHdr"   ).hide();
            jQuery("#greenHdr"  ).hide();
            jQuery("#redHdr"    ).show();
        }
        else
        {
            console.log("Bad Plane Directive: " + me.plane);
        }
    }


//  Build the control div contents

    me.makeControl = function()
    {
        if(me.debug)
            console.log("DEBUG> makeControl()");

        var controlHTML = ""

        + "<div class='planeSelect'>"
        + "    <select id='fitsPlane' class='colorPlane'>"
        + "        <option value='blue' selected='selected'>Blue</option>"
        + "        <option value='green'>Green</option>"
        + "        <option value='red'>Red</option>"
        + "    </select>"
        + "</div>"
        + "<br/>"
        + "<div id='grayHdr' class='hdrContainer'>"
        + "</div>"
        + "<div id='blueHdr' class='hdrContainer'>"
        + "</div>"
        + "<div id='greenHdr' class='hdrContainer'>"
        + "</div>"
        + "<div id='redHdr' class='hdrContainer'>"
        + "</div>";

        jQuery(me.fitsDiv).html(controlHTML);
    
        jQuery(me.fitsDiv).find('.colorPlane').change(function(){ 
      
            me.plane = jQuery(me.fitsDiv).find('.colorPlane option:selected').val();

            console.log("DEBUG> plane: " + me.plane);

            me.processUpdate();
        });

        me.viewer.client.send("header");
    }
}

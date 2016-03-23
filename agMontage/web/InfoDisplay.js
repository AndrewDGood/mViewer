/***************************************************************/
/*  File Information Display                                   */
/*                                                             */
/*  This is the Javascript for the dialog that displays        */ 
/*  information about the display mode (color vs. grayscale    */
/*  as well as the name(s) of the file(s) making up the image  */
/*  Elements in this dialog are not manipulated by the user.   */
/***************************************************************/

function InfoDisplay(displayDivName, viewer)
{
    var me = this;

    me.debug = false;

    me.displayDivName = displayDivName;

    me.displayDiv = document.getElementById(me.displayDivName);

    me.viewer = viewer;

    me.mode             = "color";
    me.gray_file_name   = "";
    me.blue_file_name   = "";
    me.green_file_name  = "";
    me.red_file_name    = "";


//  Initialize

    me.init = function()
    {
        if(me.debug)
            console.log("DEBUG> InfoDisplay.init()");

        //  if(typeof(me.viewer.colorState) == "undefined")
        //      me.initColorState();

        me.mode = me.viewer.updateJSON.display_mode;

        me.makeDisplay();
        me.processUpdate();
    }


//  This is a static display, so this functionality did not need
//  to be separated from the initialization.  Duplicating the
//  organization of the other controls' is a stylistic choice.

    me.processUpdate = function()
    {
        jQuery("#" + me.displayDivName + " .colormode" ).html(me.mode);

        if(me.mode == "color")
        {
            me.blue_file_name    = me.viewer.updateJSON.blue_file.fits_file;
            me.green_file_name   = me.viewer.updateJSON.green_file.fits_file;
            me.red_file_name     = me.viewer.updateJSON.red_file.fits_file;

            jQuery("#" + me.displayDivName + " .bluefile" ).html(me.blue_file_name);
            jQuery("#" + me.displayDivName + " .greenfile" ).html(me.green_file_name);
            jQuery("#" + me.displayDivName + " .redfile" ).html(me.red_file_name);
        }
        else
        {
            me.gray_file_name     = me.viewer.updateJSON.gray_file.fits_file;

            jQuery("#" + me.displayDivName + " .grayfile" ).html(me.gray_file_name);
        }
     }


    //  Build the control div contents

    me.makeDisplay = function()
    {
        if(me.debug)
            console.log("DEBUG> makeDisplay()");

        var displayHTML; 

        if(me.mode == "color")
        {
            displayHTML = ""

            + "<div class='infoDiv'>"
            + "    <center>"
            + "        <table border='0'>"
            + "            <tr>"
            + "                <td>"
            + "                    Mode:  "
            + "                </td>"
            + "                <td>"
            + "                    <div class='colormode'>color mode</div>"
            + "                </td>"
            + "            </tr>"
            + "            <tr>"
            + "                <td>"
            + "                    Blue File: "
            + "                </td>"
            + "                <td>"
            + "                    <div class='bluefile'>blue file name</div>"
            + "                </td>"
            + "            </tr>"
            + "            <tr>"
            + "                <td>"
            + "                    Green File: "
            + "                </td>"
            + "                <td>"
            + "                    <div class='greenfile'>green file name</div>"
            + "                </td>"
            + "            </tr>"
            + "            <tr>"
            + "                <td>"
            + "                    Red File: "
            + "                </td>"
            + "                <td>"
            + "                    <div class='redfile'>red file name</div>"
            + "                </td>"
            + "            </tr>"
            + "        </table>"
            + "    </center>"
            + "</div>";
        }
        else if(me.mode == "grayscale")
        {
            displayHTML = ""

            + "<div class='infoDiv'>"
            + "    <center>"
            + "        <table border='0'>"
            + "            <tr>"
            + "                <td>"
            + "                    Mode:  "
            + "                </td>"
            + "                <td>"
            + "                    <div class='colormode'>color mode</div>"
            + "                </td>"
            + "            </tr>"
            + "            <tr>"
            + "                <td>"
            + "                    Gray File: "
            + "                </td>"
            + "                <td>"
            + "                    <div class='grayfile'>gray file name</div>"
            + "                </td>"
            + "            </tr>"
            + "        </table>"
            + "    </center>"
            + "</div>";
        }

        if(me.debug)
            console.log("DEBUG> makeDisplay() setting HTML");

        jQuery(me.displayDiv).html(displayHTML);
    }
}

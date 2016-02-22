/****************************/
/* Zoom/Pan Control Display */
/****************************/

function ZoomControl(displayDivName, viewer)
{
    var me = this;

    me.debug = true;

    me.displayDivName = displayDivName;

    me.displayDiv = document.getElementById(me.displayDivName);

    me.viewer = viewer;

    me.init = function()
    {

        if(me.debug)
            console.log("DEBUG> ZoomControl.init()");

        me.makeDisplay();
    }


   // Build the control div contents

    me.makeDisplay = function()
    {
        var displayHTML; 

        displayHTML = ""

        + "<div class='panelDiv'>"
        + "    <table class='controlPanel'>"
        + "        <tr>"
        + "            <td>"
        + "                <button type='button' title='Pan Up/Left' style='border-top-left-radius:40px' onclick='viewer.panUpLeft()'>"
        + "                    <img src='pan_up_left.gif'/>" 
        + "                </button>"
        + "            </td>" 
        + "            <td>"
        + "                <button type='button' title='Pan Up' onclick='viewer.panUp()'>"
        + "                    <img src='pan_up.gif'/>" 
        + "                </button>"
        + "            </td>"
        + "            <td>"
        + "                <button type='button' title='Pan Up/Right'  style='border-top-right-radius:40px' onclick='viewer.panUpRight()'>"
        + "                    <img src='pan_up_right.gif'/>" 
        + "                </button>"
        + "            </td>"  
        + "        </tr>"
        + "        <tr>"
        + "            <td style='text-align: right'>"
        + "                <button type='button' title='Pan Left' onclick='viewer.panLeft()'>"
        + "                    <img src='pan_left.gif'/>" 
        + "                </button>"
        + "            </td>" 
        + "            <td>"
        + "                <button type='button' title='Jump To Image Center' onclick='viewer.center()'>"
        + "                    <img src='center_30.gif'/>" 
        + "                </button>"
        + "            </td>"
        + "            <td style='text-align: left'>"
        + "                <button type='button' title='Pan Right' onclick='viewer.panRight()'>"
        + "                    <img src='pan_right.gif'/>" 
        + "                </button>"
        + "            </td>"
        + "        </tr>"
        + "        <tr>"
        + "            <td>"
        + "                <button type='button' title='Pan Down/Left'  style='border-bottom-left-radius:40px' onclick='viewer.panDownLeft()'>"
        + "                    <img src='pan_down_left.gif'/>" 
        + "                </button>"
        + "            </td>" 
        + "            <td>"
        + "                <button type='button' title='Pan Down' onclick='viewer.panDown()'>"
        + "                    <img src='pan_down.gif'/>" 
        + "                </button>"
        + "            </td>"
        + "            <td>"
        + "                <button type='button' title='Pan Down/Right'  style='border-bottom-right-radius:40px' onclick='viewer.panDownRight()'>"
        + "                    <img src='pan_down_right.gif'/>" 
        + "                </button>"
        + "            </td>" 
        + "        </tr>"
        + "    </table>"
        + "</div>"
        + "<br></br>"
        + "<div class='panelDiv'>"
        + "    <table class='controlPanel'>"
        + "        <tr>"
        + "            <td>"
        + "                <button type='button' title='Zoom In' onclick='viewer.zoomIn()'>"
        + "                    <img src='zoom_in.gif'/>" 
        + "                </button>"
        + "            </td>" 
        + "            <td>" 
        + "                <button type='button' title='Zoom Out' onclick='viewer.zoomOut()'>"
        + "                    <img src='zoom_out.gif'/>" 
        + "                </button>" 
        + "            </td>"
        + "            <td>"
        + "                <button type='button' title='Reset Zoom' onclick='viewer.resetZoom()'>"
        + "                    <img src='zoom_reset.gif'/>" 
        + "                </button>"
        + "            </td>"
        + "        </tr>"
        + "    </table>"
        + "</div>";

        if(me.debug)
            console.log("DEBUG> makeDisplay() setting HTML");

        jQuery(me.displayDiv).html(displayHTML);
    }
}


/*****************************************************************/
/*  Layer Controls (Map Overlays)                                */
/*                                                               */
/*  This object encapsulates a control box that a user can use   */
/*  to manage a set of image overlays.  These overlays can       */
/*  include:                                                     */
/*                                                               */
/*  - Coordinate grids                                           */
/*  - Astronomical catalogs (scaled symbols)                     */
/*  - Image metadata (boxes)                                     */
/*  - Labels                                                     */
/*  - Custom markers                                             */
/*                                                               */
/*  The control allows the user to modify the details for each   */
/*  layer (e.g. color of a grid or text of a label) and arrange  */
/*  the order in which they will be drawn.  Layers can also be   */
/*  selectively shown or hidden.                                 */
/*****************************************************************/

/*****************************************************************/
/*  The current version of this control does not allow the user  */
/*  to add new overlays or delete existing overlays from the     */
/*  view object (and its associated data structure).  This is    */
/*  a possible future expansion to the interface.                */
/*****************************************************************/

function LayerControl(controlDivName, viewer)
{
    var me = this;

    me.debug = false;

    me.controlDivName = controlDivName;

    me.controlDiv = document.getElementById(me.controlDivName);

    me.viewer = viewer;


    me.init = function()
    {
    //  We separate this init() function from the object creation
    //  in case there is information the calling application wants
    //  to set in the control beyond the basic div/viewer info
    //  passed in.  In our examples this is not the case but better
    //  to be safe than sorry.  One use pattern where this might 
    //  well be the case is someone wanting to turn on control 
    //  debugging.

        if(me.debug)
            console.log("DEBUG> LayerControl.init()");

    //  Create the control div HTML content. This is 
    //  just creating a block of text and using it to 
    //  replace the (usually empty) target <div> contents.

        me.makeControl();

    //  Using the current viewer 'updateJSON' structure, 
    //  populate the layer control with the current layer
    //  info.

        var nlayer = me.viewer.updateJSON.overlay.length;

        if(me.debug)
            console.log("DEBUG> LayerControl.init(): " + nlayer + " layers");

        for(i=0; i<nlayer; ++i)
        {
            var type      = me.viewer.updateJSON.overlay[i].type;
            var coord_sys = me.viewer.updateJSON.overlay[i].coord_sys;
            var color     = me.viewer.updateJSON.overlay[i].color;

            var dataFile = me.viewer.updateJSON.overlay[i].data_file;
            var dataCol  = me.viewer.updateJSON.overlay[i].data_col;
            var dataRef  = me.viewer.updateJSON.overlay[i].data_ref;
            var dataType = me.viewer.updateJSON.overlay[i].data_type;

            var sym_type  = me.viewer.updateJSON.overlay[i].sym_type;
            var sym_size  = me.viewer.updateJSON.overlay[i].sym_size;

            var location = me.viewer.updateJSON.overlay[i].location;
            var lat = me.viewer.updateJSON.overlay[i].lat;
            var lon = me.viewer.updateJSON.overlay[i].lon;

            var text     = me.viewer.updateJSON.overlay[i].text;
            var visible  = me.viewer.updateJSON.overlay[i].visible;

            if(me.debug) 
            {
                console.log("DEBUG> ilayer= " + i);
                console.log("DEBUG> type= " + type);
                console.log("DEBUG> visible= " + visible);
            } 
         
	    switch(type)
            {
                case "grid":
                    me.addGridRec(coord_sys, color, visible);
                    break;

                case "catalog":
                    me.addCatalogRec(dataFile, dataCol, sym_type, sym_size, dataRef, dataType, color, visible);
                    break;

                case "imginfo":
                    me.addImageRec(dataFile, color, visible);
                    break;

                case "mark":
                    me.addMarkRec(coord_sys, lat, lon, sym_type, sym_size, color, visible);
                    break;

                case "label":
                    me.addLabelRec(coord_sys, lat, lon, text, color, visible);
                    break;
            
                default:
                    break;
            }
        }
    }


//  Add a "GRID" Row to the Layer Manager

    me.addGridRec = function(coord_sys, color, gridVisible)
    {
        if(me.debug) 
        {
            console.log("DEBUG> LayerControl.addGridRec()");
            console.log("DEBUG> gridVisible= " + gridVisible);
        }

        var index = jQuery(me.controlDiv).find(".overlayTbl").find("tr").size() - 1;

        jQuery(me.controlDiv).find(".overlayTbl tr:last").show();

        var clonedRow = jQuery(me.controlDiv).find(".overlayTbl tr:last").clone();

        jQuery(me.controlDiv).find(".overlayTbl").append(clonedRow);

        var row = jQuery(me.controlDiv).find(".overlayTbl").find("tr").eq(index);

        row.find(".dragOff").attr("class", "drag");

        row.find(".showOff").attr("class", "showLayer");

    //  Show/hide
        if(gridVisible) 
        {
            row.find(".showLayer").html("<input type='checkbox' checked='checked' />"); 
            if(me.debug) 
            {
                console.log("DEBUG> here1: show with checkbox");
            } 
        }
        else 
        {
            row.find(".showLayer").html("<input type='checkbox' />"); 
            if(me.debug) {
                console.log("DEBUG> here2: show without checkbox");
            } 
        }

        row.find(".type").html("GRID");

    //  Coordinate system
        row.find(".source").html(""
            + "<center><select class='coord_sys ovSelect'>\n"
            + "    <option value='eqj2000'>Equ J2000</option>\n"
            + "    <option value='eqb1950'>Equ B1950</option>\n"
            + "    <option value='gal'>Galactic</option>\n"
            + "    <option value='ecj2000'>Ecl J2000</option>\n"
            + "    <option value='ecb1950'>Ecl B1950</option>\n"
            + "</select></center>"
        );

    //  Blank non-appicable fields
        row.find(".symbol").html("&nbsp;");
        row.find(".scale").html("&nbsp;");

    //  Color
        row.find(".color").html("<input type='text' class='gridColor ovSelect'/>");

        row.find(".color").find(".gridColor").spectrum({
            preferredFormat: "hex",
            color:       color
        });


    //  Delete row from dialog (NOT CURRENTLY SHOWN)
    //-----------------------------------------------------------------------------
        row.find(".delOff").attr("class", "delete");

        row.find(".delete").click(function(){
            row.remove();
        });
    //-----------------------------------------------------------------------------


        row.find(".source").find('.coord_sys option[value="' + coord_sys + '"]').prop("selected", true);

        jQuery(me.controlDiv).find(".overlayTbl tr:last").hide();
    }


//  Add a "SOURCE TABLE" Row to the Layer Manager

    me.addCatalogRec = function(dataFile, dataCol, sym_type, sym_size, dataRef, dataType, catColor, catVisible)
    {
        if(me.debug)
            console.log("DEBUG> LayerControl.addCatalogRec()");

        var index = jQuery(me.controlDiv).find(".overlayTbl").find("tr").size() - 1;

        jQuery(me.controlDiv).find(".overlayTbl tr:last").show();

        var clonedRow = jQuery(me.controlDiv).find(".overlayTbl tr:last").clone();

        jQuery(me.controlDiv).find(".overlayTbl").append(clonedRow);

        var row = jQuery(me.controlDiv).find(".overlayTbl").find("tr").eq(index);

        row.find(".dragOff").attr("class", "drag");
        row.find(".showOff").attr("class", "showLayer");

    //  Show/hide
        if(catVisible == true)
            row.find(".showLayer").html("<input type='checkbox' checked='checked' />"); 
        else
            row.find(".showLayer").html("<input type='checkbox' />"); 

        row.find(".type").html("SOURCE<br/>TABLE");

    //  Table source (typically catalog file)
        value = "<table class='ovlyCellTbl'><tr><td style='padding: 0px 4px'><b>File:</b></td>\n";

        value += "<td style='padding: 0px 4px'><span class='fileName'>" + dataFile + "</span></td></tr>\n"

        value += "<tr><td style='padding: 0px 4px'><b>Column:</b></td>\n";

        value += "<td style='padding: 0px 4px'><span class='colName'>" + dataCol + "</span></td></tr></table>\n"

        row.find(".source").html(value);

    //  Symbol shape
        value = "<table class='ovlyCellTbl'><tr><td style='padding: 0px 4px'><b>Symbol:</b></td>\n";

        value += "<td><select class='sym_type ovSelect'>\n"
               + "    <option value='triangle'>Triangle</option>\n"
               + "    <option value='box'>Box</option>\n"
               + "    <option value='square'>Square</option>\n"
               + "    <option value='diamond'>Diamond</option>\n"
               + "    <option value='pentagon'>Pentagon</option>\n"
               + "    <option value='hexagon'>Hexagon</option>\n"
               + "    <option value='septagon'>Septagon</option>\n"
               + "    <option value='octagon'>Octagon</option>\n"
               + "    <option value='circle'>Circle</option>\n"
               + "</select></td></tr>"

               + "<tr><td style='padding: 0px 4px'><b>Size:</b></td>\n"
               + "<td><input size='8' class='sym_size ovInput' value='" + sym_size + "' /></td></tr></table>";

        row.find(".symbol").html(value);

    //  Scale
        value = "<table class='ovlyCellTbl'><tr><td style='padding: 0px 4px'><b>Type:</b></td>\n";

        value += "<td><select class='dataType ovSelect'>\n"
               + "    <option value='mag'>Mag</option>\n"
               + "    <option value='lin'>Linear</option>\n"
               + "    <option value='log'>Log</option>\n"
               + "    <option value='loglog'>Log*log</option>\n"
               + "</select></td></tr>";

        value += "<tr><td><span style='padding: 0px 4px; white-space: nowrap;'><b>Ref val:</b></span></td>\n";

        value += "<td><input class='dataRef ovInput' size='8' value='" + dataRef + "'/></td></tr></table>";

        row.find(".scale").html(value);

    //  Color
        row.find(".color").html("<input type='text' class='catColor ovSelect'/>");

        row.find(".color").find(".catColor").spectrum({
            preferredFormat: "hex",
            color:       catColor,
        });


    //  Delete row from dialog (NOT CURRENTLY SHOWN)
    //-----------------------------------------------------------------------------
        row.find(".delOff").attr("class", "delete");

        row.find(".delete").click(function(){
            row.remove();
        });
    //-----------------------------------------------------------------------------


        row.find(".symbol").find('.sym_type  option[value="' + sym_type + '"]').prop("selected", true);
        row.find(".symbol").find('.sym_size  option[value="' + sym_size + '"]').prop("selected", true);
        row.find(".scale" ).find('.dataType option[value="' + dataRef + '"]').prop("selected", true);

        jQuery(me.controlDiv).find(".overlayTbl tr:last").hide();
    }


//  Add an "IMAGE OUTLINES" Row to the Layer Manager

    me.addImageRec = function(dataFile, color, imgVisible)
    {
        if(me.debug)
            console.log("DEBUG> LayerControl.addImageRec()");

        var index = jQuery(me.controlDiv).find(".overlayTbl").find("tr").size() - 1;

        jQuery(me.controlDiv).find(".overlayTbl tr:last").show();

        var clonedRow = jQuery(me.controlDiv).find(".overlayTbl tr:last").clone();

        jQuery(me.controlDiv).find(".overlayTbl").append(clonedRow);

        var row = jQuery(me.controlDiv).find(".overlayTbl").find("tr").eq(index);

    //  Show/hide
        row.find(".dragOff").attr("class", "drag");
        row.find(".showOff").attr("class", "showLayer");

        if(imgVisible == true)
            row.find(".showLayer").html("<input type='checkbox' checked='checked' />"); 
        else
            row.find(".showLayer").html("<input type='checkbox' />"); 

        row.find(".type").html("IMAGE<br/>OUTLINES");

    //  Source file
        value = "<table class='ovlyCellTbl'><tr><td style='padding: 0px 4px'><b>File:</b></td>\n";

        value += "<td><span class='fileName' style='padding: 0px 4px'>" + dataFile + "</span></td></tr></table>\n"

        row.find(".source").html(value);

    //  Blank non-appicable fields
        row.find(".symbol").html("&nbsp;");
        row.find(".scale").html("&nbsp;");
 
    //  Color
        row.find(".color").html("<input type='text' class='imgColor ovSelect'/>");

        row.find(".color").find(".imgColor").spectrum({
            preferredFormat: "hex",
            color:       color
        });


    //  Delete row from dialog (NOT CURRENTLY SHOWN)
    //-----------------------------------------------------------------------------
        row.find(".delOff").attr("class", "delete");

        row.find(".delete").click(function(){
            row.remove();
        });
    //-----------------------------------------------------------------------------


        jQuery(me.controlDiv).find(".overlayTbl tr:last").hide();
   }


//  Add a "MARK" Row to the Layer Manager

    me.addMarkRec = function(coord_sys, lat, lon, sym_type, sym_size, color, markVisible)
    {
        if(me.debug)
            console.log("DEBUG> LayerControl.addMarkRec()");

        var index = jQuery(me.controlDiv).find(".overlayTbl").find("tr").size() - 1;

        jQuery(me.controlDiv).find(".overlayTbl tr:last").show();

        var clonedRow = jQuery(me.controlDiv).find(".overlayTbl tr:last").clone();

        jQuery(me.controlDiv).find(".overlayTbl").append(clonedRow);

        var row = jQuery(me.controlDiv).find(".overlayTbl").find("tr").eq(index);

        row.find(".dragOff").attr("class", "drag");
        row.find(".showOff").attr("class", "showLayer");

    //  Show/hide
        if(markVisible == true)
            row.find(".showLayer").html("<input type='checkbox' checked='checked' />"); 
        else
            row.find(".showLayer").html("<input type='checkbox' />"); 

        row.find(".type").html("MARK");

    //  Location
        var loc = "" + coord_sys + ": " + me.toDMS(lon) + ", " + me.toDMS(lat);

        row.find(".source").html( "<center><input size='40' class='ovInput' "
                                + "style='background-color: #d8d8d8' value='" 
                                + loc + "' readonly/></center>");

    //  Symbol type 
        row.find(".symbol").html(""
            + " <center><select class='sym_type ovSelect'>\n"
            + "     <option value='triangle'>Triangle</option>\n"
            + "     <option value='box'>Box</option>\n"
            + "     <option value='square'>Square</option>\n"
            + "     <option value='diamond'>Diamond</option>\n"
            + "     <option value='pentagon'>Pentagon</option>\n"
            + "     <option value='hexagon'>Hexagon</option>\n"
            + "     <option value='septagon'>Septagon</option>\n"
            + "     <option value='octagon'>Octagon</option>\n"
            + "     <option value='circle'>Circle</option>\n"
            + "</select></center>"
        );

    //  Size
        row.find(".scale").html("<center><input size='8' "
                              + "class='sym_size ovInput' "
                              + "value='" + sym_size + "' /></center>");

    //  Color
        row.find(".color").html("<input type='text' class='markColor ovSelect'/>");

        row.find(".color").find(".markColor").spectrum({
            preferredFormat: "hex",
            color:       color
        });


    //  Delete row from dialog (NOT CURRENTLY SHOWN)
    //-----------------------------------------------------------------------------
        row.find(".delOff").attr("class", "delete");

        row.find(".delete").click(function(){
            row.remove();
        });
    //-----------------------------------------------------------------------------


        row.find('.symbol .sym_type option[value="' + sym_type + '"]').prop("selected", true);

        jQuery(me.controlDiv).find(".overlayTbl tr:last").hide();
    }


//  Add a "LABEL" Row to the Layer Manager

    me.addLabelRec = function(coord_sys, lat, lon, text, color, labelVisible)
    {
        if(me.debug)
            console.log("DEBUG> LayerControl.addLabelRec()");

        var index = jQuery(me.controlDiv).find(".overlayTbl").find("tr").size() - 1;

        jQuery(me.controlDiv).find(".overlayTbl tr:last").show();

        var clonedRow = jQuery(me.controlDiv).find(".overlayTbl tr:last").clone();

        jQuery(me.controlDiv).find(".overlayTbl").append(clonedRow);

        var row = jQuery(me.controlDiv).find(".overlayTbl").find("tr").eq(index);

        row.find(".dragOff").attr("class", "drag");
        row.find(".showOff").attr("class", "showLayer");

    //  Show/hide
        if(labelVisible == true)
            row.find(".showLayer").html("<input type='checkbox' checked='checked' />"); 
        else
            row.find(".showLayer").html("<input type='checkbox' />"); 

        row.find(".type").html("LABEL");

    //  Location
        var loc = "" + coord_sys + ": " + me.toDMS(lon) + ", " + me.toDMS(lat);
        row.find(".source").html("<center><input size='40' class='ovInput' style='background-color: #d8d8d8' value='" + loc + "' readonly/></center>");

    //  Label text
        row.find(".symbol").html("<center><input size='20' class='ovInput' value='" + text + "' /></center>");

    //  Size
        row.find(".scale").html("&nbsp;");

    //  Color
        row.find(".color").html("<input type='text' class='labelColor ovSelect'/>");

        row.find(".color").find(".labelColor").spectrum({
            preferredFormat: "hex",
            color:       color
        });


    // Delete row from dialog (NOT CURRENTLY SHOWN)
    //-----------------------------------------------------------------------------
        row.find(".delOff").attr("class", "delete");

        row.find(".delete").click(function(){
            row.remove();
        });
    //-----------------------------------------------------------------------------


        jQuery(me.controlDiv).find(".overlayTbl tr:last").hide();
    }


//  "Update Display" button pressed

    me.updateLayers = function()
    {
        var nLayer, nOverlay;
        var ovShow, ovType, ovCsys, ovLocation, ovTable, ovSymbol;
        var ovText, ovSize, ovColumn, ovDataType, ovDataRef, ovColor;

        if(me.debug)
            console.log("DEBUG> LayerControl.updateLayers()");

        nLayer = jQuery(me.controlDiv).find(".sortable .fixed").length-1;

        if(me.debug)
            console.log(nLayer + " layers");

        nOverlay = 0;


    //  Update the "overlay" array in the view data structure (updateJSON.json)

        me.viewer.updateJSON.overlay = [];

        for(var i=0; i<nLayer; ++i)
        {
            ovShow = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".showLayer :checkbox").is(":checked");

            if(ovShow == false) ovShow = 0;
            if(ovShow == true)  ovShow = 1;

            ovType = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".type").text();

            if(me.debug)
                console.log("Layer " + i + " type: [" + ovType + "]  checked: " + ovShow);

        //  GRID 
            if(ovType == "GRID")
            {
                ovCsys  = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".source").find("select option:selected").val();

                ovColor = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".gridColor").spectrum('get').toHexString();

                if(me.debug)
                    console.log("GRID:  color = " + ovColor + ", grid = " + ovCsys);

                me.viewer.updateJSON.overlay[nOverlay] = {};

                me.viewer.updateJSON.overlay[nOverlay].type     = "grid";
                me.viewer.updateJSON.overlay[nOverlay].coord_sys = ovCsys;
                me.viewer.updateJSON.overlay[nOverlay].color    = ovColor;
                me.viewer.updateJSON.overlay[nOverlay].visible  = ovShow;

                ++nOverlay;
            }

        //  CATALOG 
            else if(ovType == "SOURCETABLE")
            {
                ovTable    = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".source .fileName").text();

                ovColumn   = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".source .colName").text();

                ovSymbol   = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".symbol").find(".sym_type").find("option:selected").val();
             
                ovSize     = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".symbol").find("input").val();
             
                ovDataType = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".scale").find(".dataType").find("option:selected").val();

                ovDataRef  = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".scale").find(".dataRef").val();
             
                ovColor    = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".catColor").spectrum('get').toHexString();

                if(me.debug)
                    console.log("CATALOG: color = " + ovColor  + ", csys = " + ovCsys + ", symbol = " + ovSymbol + ", table = " + ovTable + ", column = " + ovColumn + ", size = " + ovSize + ", type = " + ovDataType   + ", ref = " + ovDataRef);


                me.viewer.updateJSON.overlay[nOverlay] = {};

                me.viewer.updateJSON.overlay[nOverlay].type     = "catalog";
                me.viewer.updateJSON.overlay[nOverlay].coord_sys = ovCsys;
                me.viewer.updateJSON.overlay[nOverlay].color    = ovColor;
                me.viewer.updateJSON.overlay[nOverlay].dataFile = ovTable;
                me.viewer.updateJSON.overlay[nOverlay].dataCol  = ovColumn;
                me.viewer.updateJSON.overlay[nOverlay].dataRef  = ovDataRef;
                me.viewer.updateJSON.overlay[nOverlay].dataType = ovDataType;
                me.viewer.updateJSON.overlay[nOverlay].sym_type  = ovSymbol;
                me.viewer.updateJSON.overlay[nOverlay].sym_size  = ovSize;
                me.viewer.updateJSON.overlay[nOverlay].visible  = ovShow;

                ++nOverlay;
            }

        //  IMAGES 
            else if(ovType == "IMAGEOUTLINES")
            {
                ovTable = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".source .fileName").text();

                ovColor = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".imgColor").spectrum('get').toHexString();

                if(me.debug)
                    console.log("IMAGES: color = " + ovColor + ", table = " + ovTable );

                me.viewer.updateJSON.overlay[nOverlay] = {};

                me.viewer.updateJSON.overlay[nOverlay].type     = "imginfo";
                me.viewer.updateJSON.overlay[nOverlay].color    = ovColor;
                me.viewer.updateJSON.overlay[nOverlay].dataFile = ovTable;
                me.viewer.updateJSON.overlay[nOverlay].visible  = ovShow;

                ++nOverlay;
            }

        //  MARK  
            else if(ovType == "MARK")
            {
                ovLocation = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".source").find("input").val();

                ovSymbol    = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".symbol").find("select option:selected").val();

                ovSize      = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".scale").find("input").val();

                ovColor     = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".markColor").spectrum('get').toHexString();

                if(me.debug)
                    console.log("MARK: color = " + ovColor + ", location = " + ovLocation + ", symbol = " + ovSymbol + ", size = " + ovSize );

                me.viewer.updateJSON.overlay[nOverlay] = {};

                me.viewer.updateJSON.overlay[nOverlay].type     = "mark";
                me.viewer.updateJSON.overlay[nOverlay].color    = ovColor;
                me.viewer.updateJSON.overlay[nOverlay].sym_type  = ovSymbol;
                me.viewer.updateJSON.overlay[nOverlay].sym_size  = ovSize;
                me.viewer.updateJSON.overlay[nOverlay].location = ovLocation;
                me.viewer.updateJSON.overlay[nOverlay].visible  = ovShow;

                ++nOverlay;
            }

        //  LABEL 
            else if(ovType == "LABEL")
            {
                ovLocation = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".source").find("input").val();

                ovText     = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".symbol").find("input").val();

                ovColor    = jQuery(me.controlDiv).find(".sortable .fixed").eq(i).find(".labelColor").spectrum('get').toHexString();

                if(me.debug && ovText.length > 0)
                    console.log("LABEL: color = " + ovColor + ", location = " + ovLocation + ", text = " + ovText );

                me.viewer.updateJSON.overlay[nOverlay] = {};

                me.viewer.updateJSON.overlay[nOverlay].type     = "label";
                me.viewer.updateJSON.overlay[nOverlay].color    = ovColor;
                me.viewer.updateJSON.overlay[nOverlay].location = ovLocation;
                me.viewer.updateJSON.overlay[nOverlay].text     = ovText;
                me.viewer.updateJSON.overlay[nOverlay].visible  = ovShow;

                ++nOverlay;
            }
        }

        me.viewer.grayOut(true, {'opacity':'50'});
        me.viewer.grayOutMessage(true);

        me.viewer.submitUpdateRequest();
    }


//  Build the control div contents.

    me.makeControl = function()
    {
        if(me.debug)
            console.log("DEBUG> LayerControl.makeControl()");

        var controlHTML = ""

        + "<center>"
        + "<div id='layerset' class='layerDiv'>"
        + "<fieldset class='fieldset'>"
        + "    <div>"
        + "    <table class='overlayTbl'>"
        + "        <thead>"
        + "            <tr>"
        //  + "                <td class='ovlyhdSmall'>move</td>"
        + "                <td class='ovlyhdSmall'>"
        + "                    <img src='eye02_22.gif'/>" 
        + "                </td>"
        + "                <td class='ovlyhd'>Overlay Type</td>"
        + "                <td class='ovlyhd'>Data Source / Location</td>"
        + "                <td class='ovlyhd'>Symbol / Text</td>"
        + "                <td class='ovlyhd'>Scale</td>"
        + "                <td class='ovlyhd'>Color</td>"
        //  + "                <td class='ovlyhdSmall'>del</td>"
        + "            </tr>"
        + "        </thead>"
        + "        <tbody class='sortable'>"
        + "            <tr class='fixed'>"
        //  + "                <td class='dragOff'>&nbsp;</td>"
        + "                <td class='showOff'>&nbsp;</td>"
        + "                <td class='type'>&nbsp;</td>"
        + "                <td class='source'> &nbsp; </td>"
        + "                <td class='symbol'> &nbsp; </td>"
        + "                <td class='scale'> &nbsp; </td>"
        + "                <td class='color'> &nbsp; </td>"
        //  + "                <td class='delOff'>&nbsp;</td>"
        + "            </tr>"
        + "        </tbody>"
        + "    </table>"
        + "    </div>"
        + "</fieldset>"
        + "</div>"

        //  + "<br/><input type='submit' class='updateBtn' value='Update Display'>"
        + "<br/>"
        + "<button style='width: 80%' type='button' onClick='layerControl.updateLayers()'>"
        + "    Update Display"
        + "</button>"
        + "<br/>"
        + "</center>";

        if(me.debug)
            console.log("DEBUG> LayerControl.makeControl(): setting HTML");

        jQuery(me.controlDiv).html(controlHTML);

        //  jQuery(me.controlDiv).find(".updateBtn").click(me.updateLayers);

        jQuery(me.controlDiv).find(".sortable").sortable({ axis: "y", tolerance: "pointer", containment: "parent", cursor: "move", delay: 150, handle: ".drag" });
    }


//  Convert (float) values of coordinates (for markers, labels, etc.)
//  to degree/minute/second values, to be more useful to astronomers 
//  and 16th century frigate navigators.

    me.toDMS = function(coordinate)
    {
        var sign

        if(coordinate < 0)
            sign = "-"
        else
            sign = ""

        var c = Math.abs(coordinate)
        var deg = Math.floor (c);
        var minfloat = (c-deg)*60;
        var min = Math.floor(minfloat);
        var secfloat = (minfloat-min)*60;
        var sec = Math.round(secfloat);

        if (sec==60) {
            min++;
            sec=0;
        }

        if (min==60) {
            deg++;
            min=0;
        }

        return ("" + sign + deg + "d" + min + "m" + sec + "s");
    }
}

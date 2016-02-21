/**********************/
/* FITS Header Viewer */
/**********************/

function FITSHeaderViewer(fitsDivName, viewer)
{
   var me = this;

   me.fitsDivName = fitsDivName;

   me.fitsDiv = document.getElementById(me.fitsDivName);

   me.viewer = viewer;

   me.workspace;
   me.fitsFile;

   me.mode = "color";
   me.plane = "blue";

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


   // Build the control div contents

   me.makeControl = function()
   {
      if(me.debug)
         console.log("DEBUG> makeControl()");

      var controlHTML = ""

      /*
      + "<table class = 'displayTable'> "
      + "<tr> "
      + "<td> "
      */

      + "   <div class='planeSelect'>"
      + "      <select id='fitsPlane' class='colorPlane'>"
      + "          <option value='blue' selected='selected'>Blue</option>"
      + "          <option value='green'>Green</option>"
      + "          <option value='red'>Red</option>"
      + "      </select>"
      + "   </div>"
      + "   <br/>"

      /*
      + "</td> "
      + "</tr> "

      + "<tr> "
      + "<td> "
      */

      + "   <div id='grayHdr' class='hdrContainer'>"
      + "   </div>"

      + "   <div id='blueHdr' class='hdrContainer'>"
      + "   </div>"

      + "   <div id='greenHdr' class='hdrContainer'>"
      + "   </div>"

      + "   <div id='redHdr' class='hdrContainer'>"
      + "   </div>"

      /*
      + "</td> "
      + "</tr> "

      + "</table>";
      */

      jQuery(me.fitsDiv).html(controlHTML);
    
      jQuery(me.fitsDiv).find('.colorPlane').change(function(){ 
      
         me.plane = jQuery(me.fitsDiv).find('.colorPlane option:selected').val();

         console.log("DEBUG> plane: " + me.plane);

         me.processUpdate();
      });

      me.viewer.client.send("header");
   }
}

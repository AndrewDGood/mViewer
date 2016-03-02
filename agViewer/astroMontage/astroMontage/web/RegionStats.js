/*****************************/
/* Region Statistics Display */
/*****************************/

function RegionStats(statsDivName, viewer)
{
   var me = this;

   me.statsDivName = statsDivName;

   me.statsDiv = document.getElementById(me.statsDivName);

   me.viewer = viewer;
   //me.fitsFile;

   me.plane = 'blue';

   me.statsResponse;
   me.statsJSON = {};

   me.fluxref  = 0;
   me.sigmaref = 0;
   me.xref     = 0;
   me.yref     = 0;
   me.raref    = 0;
   me.decref   = 0;
   me.fluxmin  = 0;
   me.sigmamin = 0;
   me.xmin     = 0;
   me.ymin     = 0;
   me.ramin    = 0;
   me.decmin   = 0;
   me.fluxmax  = 0;
   me.sigmamax = 0;
   me.xmax     = 0;
   me.ymax     = 0;
   me.ramax    = 0;
   me.decmax   = 0;
   me.aveflux  = 0;
   me.rmsflux  = 0;
   me.radius   = 0;
   me.radpix   = 0;
   me.npixel   = 0;
   me.nnull    = 0;


   // Initialize the 

   me.init = function()
   {
      me.updateJSON  = me.viewer.updateJSON;

      if(typeof me.viewer.pickJSON != 'undefined')
      {
         me.pickJSON  = me.viewer.pickJSON;
      
         me.makeControl();
         me.updateStats();
      }
   }


   // Update the contents of the pick dialog 

   me.updateStats = function(x, y)
   {
      var index = 0;

      if(me.plane == "blue")
      {
         index = 0;
      }
      else if(me.plane == "green")
      {
         index = 1;
      }
      else if(me.plane == "red")
      {
         index = 2;
      }

      me.statsJSON = me.viewer.pickJSON[index];

      me.factor = me.updateJSON.factor;

      me.fluxref  = me.statsJSON.fluxref;
      me.sigmaref = me.statsJSON.sigmaref;
      me.xref     = Math.round(me.updateJSON.xmin + (me.statsJSON.xref * me.factor));
      me.yref     = Math.round(me.updateJSON.ymin + (me.statsJSON.yref * me.factor));
      me.raref    = me.statsJSON.raref;
      me.decref   = me.statsJSON.decref;
      me.fluxmin  = me.statsJSON.fluxmin;
      me.sigmamin = me.statsJSON.sigmamin;
      me.xmin     = Math.round(me.updateJSON.xmin + (me.statsJSON.xmin * me.factor));
      me.ymin     = Math.round(me.updateJSON.ymin + (me.statsJSON.ymin * me.factor));
      me.ramin    = me.statsJSON.ramin;
      me.decmin   = me.statsJSON.decmin;
      me.fluxmax  = me.statsJSON.fluxmax;
      me.sigmamax = me.statsJSON.sigmamax;
      me.xmax     = Math.round(me.updateJSON.xmin + (me.statsJSON.xmax * me.factor));
      me.ymax     = Math.round(me.updateJSON.ymin + (me.statsJSON.ymax * me.factor)); 
      // me.xmax     = me.statsJSON.xmax;
      // me.ymax     = me.statsJSON.ymax;
      me.ramax    = me.statsJSON.ramax;
      me.decmax   = me.statsJSON.decmax;
      me.aveflux  = me.statsJSON.aveflux;
      me.rmsflux  = me.statsJSON.rmsflux;
      me.radius   = me.statsJSON.radius;
      me.radpix   = me.statsJSON.radpix;
      me.npixel   = me.statsJSON.npixel;
      me.nnull    = me.statsJSON.nnull;


      jQuery(me.statsDiv).find(".fluxref" ).html(me.fluxref);
      jQuery(me.statsDiv).find(".sigmaref").html(me.sigmaref);
      jQuery(me.statsDiv).find(".xref"    ).html(me.xref);
      jQuery(me.statsDiv).find(".yref"    ).html(me.yref);
      jQuery(me.statsDiv).find(".raref"   ).html(me.raref);
      jQuery(me.statsDiv).find(".decref"  ).html(me.decref);
      jQuery(me.statsDiv).find(".fluxmin" ).html(me.fluxmin);
      jQuery(me.statsDiv).find(".sigmamin").html(me.sigmamin);
      jQuery(me.statsDiv).find(".xmin"    ).html(me.xmin);	
      jQuery(me.statsDiv).find(".ymin"    ).html(me.ymin);
      jQuery(me.statsDiv).find(".ramin"   ).html(me.ramin);
      jQuery(me.statsDiv).find(".decmin"  ).html(me.decmin);
      jQuery(me.statsDiv).find(".fluxmax" ).html(me.fluxmax);
      jQuery(me.statsDiv).find(".sigmamax").html(me.sigmamax);
      jQuery(me.statsDiv).find(".xmax"    ).html(me.xmax);
      jQuery(me.statsDiv).find(".ymax"    ).html(me.ymax);
      jQuery(me.statsDiv).find(".ramax"   ).html(me.ramax);
      jQuery(me.statsDiv).find(".decmax"  ).html(me.decmax);
      jQuery(me.statsDiv).find(".aveflux" ).html(me.aveflux);
      jQuery(me.statsDiv).find(".rmsflux" ).html(me.rmsflux);
      jQuery(me.statsDiv).find(".radius"  ).html(me.radius);
      jQuery(me.statsDiv).find(".radpix"  ).html(me.radpix);
      jQuery(me.statsDiv).find(".npixel"  ).html(me.npixel);
      jQuery(me.statsDiv).find(".nnull"   ).html(me.nnull);

   }


   // Build the control div contents

   me.makeControl = function()
   {
      if(me.debug)
         console.log("DEBUG> makeControl()");

      var controlHTML = ""

      + "<div class='rsPlaneSelect'>"
      + "   <center>"
      + "      <span>"
      + "         <select class='colorPlane'>"
      + "            <option value='blue' selected='selected'>Blue Plane</option>"
      + "            <option value='green'                   >Green Plane</option>"
      + "            <option value='red'                     >Red Plane</option>"
      + "         </select>"
      + "      </span>"

      // + "      &nbsp;&nbsp;&nbsp;"
      // + "      <span class='fileName'></span>"
      // + "      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
      // + "      Radius: <input class='radius' value='20' size='5'/> pixels"

      + "   </center>"
      + "</div>"
      
      + "<br/>"

      + "<div class='statsDiv'>"
      + "   <center>"
      + "      <table class='stat'>"
      + "         <tbody>"
      + "            <tr>"
      + "               <th>&nbsp;</th>"
      + "               <th colspan='2'>FITS Image Coordinates</th>"
      + "               <th colspan='2'>Astronomical<br/>Coordinates</th>"
      + "               <th colspan='2'>Statistics</th>"
      + "            </tr>"
      + "            <tr>"
      + "               <th>&nbsp;</th>"
      + "               <th>X</th>"
      + "               <th>Y</th>"
      + "               <th>RA</th>"
      + "               <th>Dec</th>"
      + "               <th>Flux</th>"
      + "               <th>Sigma</th>"
      + "            </tr>"
      + "            <tr>"
      + "               <td><b>Center:</b></td>"
      + "               <td class='xref'></td>"
      + "               <td class='yref'></td>"
      + "               <td class='raref'></td>"
      + "               <td class='decref'></td>"
      + "               <td class='fluxref'></td>"
      + "               <td class='sigmaref'></td>"
      + "            </tr>"
      + "            <tr>"
      + "               <td><b>Max Flux:</b></td>"
      + "               <td class='xmax'></td>"
      + "               <td class='ymax'></td>"
      + "               <td class='ramax'></td>"
      + "               <td class='decmax'></td>"
      + "               <td class='fluxmax'></td>"
      + "               <td class='sigmamax'></td>"
      + "            </tr>"
      + "            <tr>"
      + "               <td><b>Min Flux:</b></td>"
      + "               <td class='xmin'></td>"
      + "               <td class='ymin'></td>"
      + "               <td class='ramin'></td>"
      + "               <td class='decmin'></td>"
      + "               <td class='fluxmin'></td>"
      + "               <td class='sigmamin'></td>"
      + "            </tr>"
      + "         </tbody>"
      + "      </table><br/>"

      + "      <table class='substat'>"
      + "         <tr>"
      + "            <td><b>Avg:</b></td>"
      + "            <td><span class='aveflux'></span> &plusmn; <span class='rmsflux'></span></td>"
      + "         </tr>"
      + "         <tr>"
      + "            <td><b>Region:</b></td>"
      + "            <td> Radius <span class='radius'></span> deg&nbsp;&nbsp;(<span class='radpix'></span> pixels)</td>"
      + "         </tr>"
      + "         <tr>"
      + "            <td>&nbsp;</td>"
      + "            <td> <span class='npixel'></span> pixels (<span class='nnull'></span> nulls)</td>"
      + "         </tr>"
      + "      </table>"
      + "      <br/>"
      + "   </center>"
      + "</div>";

      if(me.debug)
         console.log("DEBUG> makeControl() setting HTML");

      jQuery(me.statsDiv).html(controlHTML);


      // Remove color plane select box if image is grayscale

      if(me.updateJSON.display_mode == 'grayscale')
         jQuery(me.statsDiv).find('.colorPlane').hide();


      // Callback when new plane selected

      jQuery(me.statsDiv).find('.colorPlane').change(function(){

         me.plane = jQuery(me.statsDiv).find('.colorPlane option:selected').val();
         me.updateStats();

      });

      /*
      // Callback when new radius selected

      jQuery(me.statsDiv).find('.radius').change(function(){
         me.getStats(me.viewer.statsState.x, me.viewer.statsState.y);
      });
      */
   }
}

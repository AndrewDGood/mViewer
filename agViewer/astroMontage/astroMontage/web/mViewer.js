/*******************************************************************/
/* This is the Javascript for talking to the server (Python)       */
/* mViewer code.  It deals with canvas resizes, zooming, and picks */
/* and acts as a passthrough for other request (e.g. stretching)   */
/*******************************************************************/

function mViewer(client, imgDivID)
{
   var me = this;

   me.debug = true;

   me.client = client;

   me.timeoutVal = 150;


   me.imgDiv = document.getElementById(imgDivID);

   me.display = jQuery('<div/>').appendTo(me.imgDiv);

   me.display = jQuery(me.display).get(0);

   me.gc = new iceGraphics(me.display);

   me.canvasWidth  = jQuery(me.imgDiv).width();
   me.canvasHeight = jQuery(me.imgDiv).height();

   me.jsonText;
   me.updateJSON;
   me.pickJSON;

   me.currentX   = 0;
   me.currentY   = 0;   
   me.currentRA  = 0;
   me.currentDec = 0;

   me.updateCallbacks = [];

   var resizeTimeout = 0;


   // Window resizing can cause some overloading since the
   // resize events happen more rapidly than the back-end can
   // regenerate the image.  To avoid this, we use the trick of
   // having the window resize trigger a timer which then gets 
   // reinitialized if another resize event come along or, if the
   // user pauses in their resizing, calls a true "resizeFinal"
   // method which contacts the back-end.

   me.resize = function()
   {
      if(me.debug)
         console.log("DEBUG> mViewer.resize()");

      if(resizeTimeout)
         clearTimeout(resizeTimeout);

      resizeTimeout = setTimeout(me.resizeFinal, me.timeoutVal);
   }


   // This is the "resizeFinal" code, which sends a "resize <windth> <height>"
   // command to the back-end Python code.

   me.resizeFinal = function()
   {
      if(me.debug)
         console.log("DEBUG> mViewer.resizeFinal()");

      me.grayOut(true);
      me.grayOutMessage(true);

      areaWidth  = jQuery(me.imgDiv).width();
      areaHeight = jQuery(me.imgDiv).height();

      jQuery(me.display).height(areaHeight);
      jQuery(me.display).width (areaWidth);

      if(me.gc != null)
      {
         me.gc.clear();
         me.gc.refitCanvas();
      }

      me.canvasWidth  = jQuery(me.imgDiv).width();
      me.canvasHeight = jQuery(me.imgDiv).height();

      var cmd = "resize "
              + me.canvasWidth  + " "
              + me.canvasHeight + " ";

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
   }


   me.addUpdateCallback = function(fName)
   {
      me.updateCallbacks.push(fName);
   }


   // When commands like "resize" or "zoom" are sent to the back-end
   // they ultimately result in a return request to the Javascript asking
   // it to display an updated image, update the display in some other
   // way, or shut down.

   me.processUpdate = function(cmd)
   {
      if(me.debug)
         console.log("DEBUG> Processing: " + cmd);

      args = cmd.split(" ");

      var cmd = args[0];

      console.log(cmd);

      if(cmd == "image")
      {
         me.gc.clear();

         me.gc.refitCanvas();

         if(me.debug)
            console.log("DEBUG> Retrieving new JPEG.");

         me.gc.setImage(args[1] + "?seed=" + (new Date()).valueOf());

         me.getJSON();
      }

      else if(cmd == "pick")
      {
         me.getPick();
      }

      else if(cmd == "header")
      {
         me.getHeader(args[1]);
      }

      else if(cmd == "updateDisplay")
      {
         if(me.debug)
            console.log("DEBUG> Requesting server update.");

         var cmd = "update";

         if(me.debug)
            console.log("DEBUG> cmd: " + cmd);

         me.client.send(cmd);
      }

      else if(cmd == "close")
      {
         window.close();
      }
   }


   me.getJSON = function()
   {
      var xmlhttp;
      var jsonURL;

      if(me.debug)
         console.log("DEBUG> getJSON()");

      jsonURL = "view.json?seed=" + (new Date()).valueOf();

      try {
         xmlhttp = new XMLHttpRequest();
      }
      catch (e) {
         xmlhttp=false;
      }

      if (!xmlhttp && window.createRequest)
      {
         try {
            xmlhttp = window.createRequest();
         }
         catch (e) {
            xmlhttp=false;
         }
      }

      xmlhttp.open("GET", jsonURL);

      xmlhttp.send(null);

      xmlhttp.onreadystatechange = function()
      {
         if (xmlhttp.readyState==4 && xmlhttp.status==200)
         {
            me.jsonText = xmlhttp.responseText;

            me.updateJSON = jQuery.parseJSON(xmlhttp.responseText);

   	        for(i=0; i<me.updateCallbacks.length; ++i)
            {
                me.updateCallbacks[i]();
            }
         }

         else if(xmlhttp.status != 200)
            alert("Remote service error[1].");
      }
   }


   me.getPick = function()
   {
      var xmlhttp;

      var jsonURL;

      if(me.debug)
         console.log("DEBUG> getPick()");

      jsonURL = "pick.json?seed=" + (new Date()).valueOf();

      try {
         xmlhttp = new XMLHttpRequest();
      }
      catch (e) {
         xmlhttp=false;
      }

      if (!xmlhttp && window.createRequest)
      {
         try {
            xmlhttp = window.createRequest();
         }
         catch (e) {
            xmlhttp=false;
         }
      }

	  xmlhttp.open("GET", jsonURL);
	 
	  console.log("jsonURL: " + jsonURL);			   		   

	  xmlhttp.send(null);

	  xmlhttp.onreadystatechange = function()
	  {
		 if (xmlhttp.readyState==4 && xmlhttp.status==200)
		 {
			me.jsonText = xmlhttp.responseText;

			me.pickJSON = jQuery.parseJSON(xmlhttp.responseText);
		 
			console.log("pickJSON: " + me.pickJSON);		   		   
		 }
		 else if(xmlhttp.status != 200)
		 {
			alert("Remote service error[1].");
		 }
   
         statsDisplay.init();

         me.currentX   = statsDisplay.xref;
         me.currentY   = statsDisplay.yref;         
         me.currentRA  = statsDisplay.raref;
         me.currentDec = statsDisplay.decref;

         jQuery("#currentPickX").html(me.currentRA);
         jQuery("#currentPickY").html(me.currentDec);
	  }
      
   }


   me.getHeader = function(mode)
   {
      console.log("Mode: " + mode);

      if (mode == "gray")
      {
          headerURL = "header0.html?seed=" + (new Date()).valueOf();
          jQuery("#grayHdr").load(headerURL);
      }
      else if (mode == "color")
      {
          headerURL = "header0.html?seed=" + (new Date()).valueOf();
          jQuery("#blueHdr").load(headerURL);

          headerURL = "header1.html?seed=" + (new Date()).valueOf();
          jQuery("#greenHdr").load(headerURL);

          headerURL = "header2.html?seed=" + (new Date()).valueOf();
          jQuery("#redHdr").load(headerURL);

          console.log(headerURL);
      }
      else
      {
          console.log("Bad Header Directive: " + mode);
      }
      
   }


   // Any number of controls may modify the JSON view structure
   // then call this routine to have it sent to the server to have
   // the image updated.

   me.submitUpdateRequest = function()
   {
      if(me.debug)
         console.log("DEBUG> mViewer.submitUpdateRequest()");

      var cmd = "submitUpdateRequest '" + JSON.stringify(me.updateJSON) + "'";

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
      
   }


   // When the user draws a box on the screen, the most
   // common reaction is to ask the server to zoom the 
   // image based on that box.

   me.zoomCallback = function(xmin, ymin, xmax, ymax)
   {
      var tmp;

      if(me.debug)
         console.log("DEBUG> mViewer.zoomCallback()");

      me.grayOutMessage(true);
      me.grayOut(true);

      if(xmin > xmax)
      {
         tmp  = xmin;
         xmin = xmax;
         xmax = tmp;
      }

      if(xmin == xmax)
         xmax = xmin + 1.e-9;


      me.canvasWidth  = jQuery(me.imgDiv).width();
      me.canvasHeight = jQuery(me.imgDiv).height();

      ymin = (me.canvasHeight - ymin);
      ymax = (me.canvasHeight - ymax);

      if(ymin > ymax)
      {
         tmp  = ymin;
         ymin = ymax;
         ymax = tmp;
      }

      if(ymin == ymax)
         ymax = ymin + 1.e-9;


      if((ymax-ymin)<5 && (xmax-xmin)<5)
      {
         me.grayOutMessage(false);
         me.grayOut(false);

         me.gc.clearDrawing();

         // An ultra-small zoom box is almost certainly a misinterpreted "pick" 

         var cmd = "pick "
              + xmax + " "
              + ymax;

         if(me.debug)
            console.log("DEBUG> small box: " + cmd);

         me.client.send(cmd);

         return;
      }

      if(me.debug)
      {
         console.log("DEBUG> min (screen): " + xmin + ", " + ymin);
         console.log("DEBUG> max (screen): " + xmax + ", " + ymax);
      }

      var cmd = "zoom "
              + xmin + " "
              + xmax + " "
              + ymin + " "
              + ymax;

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
   }


   // Special buttons are provided for resetting the zoom,
   // zooming in and zooming out.

   me.resetZoom = function()
   {
      var tmp;

      if(me.debug)
         console.log("DEBUG> mViewer.resetZoom()");

      me.grayOutMessage(true);
      me.grayOut(true);

      var cmd = "zoomReset"

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
   }

   me.zoomIn = function()
   {
      var tmp;

      if(me.debug)
         console.log("DEBUG> mViewer.zoomIn()");

      me.grayOutMessage(true);
      me.grayOut(true);

      var cmd = "zoomIn"

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
   }


   me.zoomOut = function()
   {
      var tmp;

      if(me.debug)
         console.log("DEBUG> mViewer.zoomOut()");

      me.grayOutMessage(true);
      me.grayOut(true);

      var cmd = "zoomOut"

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
   }


   // Special buttons are provided for panning up, down, left, right
   // and diagonally between said directions.

   me.panUp = function()
   {
      var tmp;

      if(me.debug)
         console.log("DEBUG> mViewer.panUp()");

      me.grayOutMessage(true);
      me.grayOut(true);

      var cmd = "panUp"

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
   }


   me.panDown = function()
   {
      var tmp;

      if(me.debug)
         console.log("DEBUG> mViewer.panDown()");

      me.grayOutMessage(true);
      me.grayOut(true);

      var cmd = "panDown"

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
   }


   me.panLeft = function()
   {
      var tmp;

      if(me.debug)
         console.log("DEBUG> mViewer.panLeft()");

      me.grayOutMessage(true);
      me.grayOut(true);

      var cmd = "panLeft"

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
   }


   me.panRight = function()
   {
      var tmp;

      if(me.debug)
         console.log("DEBUG> mViewer.panRight()");

      me.grayOutMessage(true);
      me.grayOut(true);

      var cmd = "panRight"

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
   }


   me.panUpLeft = function()
   {
      var tmp;

      if(me.debug)
         console.log("DEBUG> mViewer.panUpLeft()");

      me.grayOutMessage(true);
      me.grayOut(true);

      var cmd = "panUpLeft"

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
   }


   me.panUpRight = function()
   {
      var tmp;

      if(me.debug)
         console.log("DEBUG> mViewer.panUpRight()");

      me.grayOutMessage(true);
      me.grayOut(true);

      var cmd = "panUpRight"

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
   }


   me.panDownLeft = function()
   {
      var tmp;

      if(me.debug)
         console.log("DEBUG> mViewer.panDownLeft()");

      me.grayOutMessage(true);
      me.grayOut(true);

      var cmd = "panDownLeft"

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
   }


   me.panDownRight = function()
   {
      var tmp;

      if(me.debug)
         console.log("DEBUG> mViewer.panDownRight()");

      me.grayOutMessage(true);
      me.grayOut(true);

      var cmd = "panDownRight"

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
   }


   // Jump to center of image (without changing zoom scale)

   me.center = function()
   {
      var tmp;

      if(me.debug)
         console.log("DEBUG> mViewer.center()");

      me.grayOutMessage(true);
      me.grayOut(true);

      var cmd = "center"

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd);

      me.client.send(cmd);
   }


   // Show color stretch dialog

   me.showColorStretch = function()
   {
      console.log("DEBUG> showColorStretch()");

      colorStretch.init();

      stretchDiv.dialog({
         autoOpen:  false,
         resizable: false,
         width:'auto'
      });

      if(stretchDiv.dialog("isOpen")==true)
      {
         stretchDiv.dialog("moveToTop");
      }
      else
      {
         stretchDiv.parent().position({
            my: "center",
            at: "center",
            of: window
         });

         jQuery("#stretch").dialog("open");
      }
   }


   // Show layer control (overlay) dialog 

   me.showOverlay = function()
   {
      console.log("DEBUG> showOverlay()");

      layerControl.init();

      layerDiv.dialog({
         autoOpen:  false,
         resizable: true,
         width:'auto',
         // height: 300,
      });

      if(layerDiv.dialog("isOpen")==true)
      {
         layerDiv.dialog("moveToTop");
      }
      else
      {
         layerDiv.parent().position({
            my: "center",
            at: "center",
            of: window
         });

         jQuery("#overlay").dialog("open");
      }
   }


   // Show region statistics dialog (mExamine results) 

   me.showStats = function()
   {
      console.log("DEBUG> showStats()");

      me.getPick();
      
      console.log("DEBUG> open stats dialog");       

      statsDiv.dialog({
         autoOpen:  false,
         resizable: false,
         // width:'auto'
         width:  520,     // manually determined width
         // height: 400     
      });

      if(statsDiv.dialog("isOpen")==true)
      {
         statsDiv.dialog("moveToTop");
         console.log("DEBUG> stats is open")
      }
      else
      {
         console.log("DEBUG> stats is not open")

/*
         statsDiv.parent().position({
            my: "center",
            at: "center",
            of: window
         });
*/
         jQuery("#stats").dialog("option", "position", { 
            my: "center", 
            at: "center", 
            of: window
         });

         // statsDiv.dialog("open");
         jQuery("#stats").dialog("open");
      }
   }


   me.showHeader = function()
   {
      console.log("DEBUG> showHeader()");
      
      headerDisplay.init();

      console.log("DEBUG> open fitsheader dialog");       

      fitsDiv.dialog({
         autoOpen:  false,
         resizable: false,
         width:'auto'
      });

      if(fitsDiv.dialog("isOpen")==true)
      {
         fitsDiv.dialog("moveToTop");
      }
      else
      {
         fitsDiv.parent().position({
            my: "center",
            at: "center",
            of: window
         });

         jQuery("#fitsheader").dialog("open");
      }
   }


   me.showInfoDisplay = function()
   {
      console.log("DEBUG> showInfoDisplay()");
      
      infoDisplay.init();

      infoDiv.dialog({
         autoOpen:  false,
         resizable: true,
         width:'auto'
      });

      if(infoDiv.dialog("isOpen")==true)
      {
         infoDiv.dialog("moveToTop");
      }
      else
      {
         infoDiv.parent().position({
            my: "center",
            at: "center",
            of: window
         });

         jQuery("#infoArea").dialog("open");
      }
   }


   me.showZoomControl = function()
   {
      console.log("DEBUG> showZoomControl()");
      
      zoomControl.init();

      zoomDiv.dialog({
         autoOpen:  false,
         resizable: false,
         width:'auto'
      });

      if(zoomDiv.dialog("isOpen")==true)
      {
         zoomDiv.dialog("moveToTop");
      }
      else
      {

/*
         zoomDiv.parent().position({
            my: "left bottom",
            at: "left bottom",
            of: window
         });
*/

/*
         zoomDiv.parent().position({
            my: "left bottom",
            at: "left bottom",
            of: window
         });
*/
         jQuery("#zoomControl").dialog("option", "position", { 
            my: "left top", 
            at: "right-190 bottom-420", 
            of: window
         });

         jQuery("#zoomControl").dialog("open");
      }
   }

   // If there are any registered update callbacks, 
   // we call them here.

   me.clickCallback = function(x, y)
   {
      me.canvasWidth  = jQuery(me.imgDiv).width();
      me.canvasHeight = jQuery(me.imgDiv).height();

      y = (me.canvasHeight - y);

      var cmd = "pick "
              + x + " "
              + y;

      if(me.debug)
         console.log("DEBUG> cmd: " + cmd + " " + x + " " + y);

      me.client.send(cmd);
   }


   // For now, we will stub out right click

   me.rightClickCallback = function(x, y)
   {
      // Do nothing.
   }


   me.gc.boxCallback        = me.zoomCallback;
   me.gc.clickCallback      = me.clickCallback;
   me.gc.rightClickCallback = me.rightClickCallback;



   /* Gray-Out Functions */

   me.grayOut = function(vis, options)
   {
      // Pass true to gray out screen, false to ungray.  Options are optional.
      // This is a JSON object with the following (optional) properties:
      //
      //    opacity:0-100         // Lower number = less grayout higher = more of a blackout
      //    zindex: #             // HTML elements with a higher zindex appear on top of the gray out
      //    bgcolor: (#xxxxxx)    // Standard RGB Hex color code
      //
      // e.g.,  me.grayOut(true, {'zindex':'50', 'bgcolor':'#0000FF', 'opacity':'70'});
      //
      // Because 'options' is JSON, opacity/zindex/bgcolor are all optional and can appear
      // in any order.  Pass only the properties you need to set.

      var options = options || {};
      var zindex  = options.zindex || 5000;
      var opacity = options.opacity || 70;
      var opaque  = (opacity / 100);
      var bgcolor = options.bgcolor || '#000000';

      var dark = document.getElementById('darkenScreenObject');

      if(!dark)
      {
         // The dark layer doesn't exist, it's never been created.  So we'll
         // create it here and apply some basic styles.

         var tbody = document.getElementsByTagName("body")[0];

         var tnode = document.createElement('div');

         tnode.style.position ='absolute';             // Position absolutely
         tnode.style.top      ='0px';                  // In the top
         tnode.style.left     ='0px';                  // Left corner of the page
         tnode.style.overflow ='hidden';               // Try to avoid making scroll bars
         tnode.style.display  ='none';                 // Start out Hidden
         tnode.id             ='darkenScreenObject';   // Name it so we can find it later

         tbody.appendChild(tnode);                     // Add it to the web page

         dark = document.getElementById('darkenScreenObject');  // Get the object.
      }


      if(vis)
      {
         // Calculate the page width and height

         if( document.body && ( document.body.scrollWidth || document.body.scrollHeight ) )
         {
            var pageWidth  =  document.body.scrollWidth+'px';
            var pageHeight = (document.body.scrollHeight+1000)+'px';
         }
         else if( document.body.offsetWidth )
         {
            var pageWidth  =  document.body.offsetWidth+'px';
            var pageHeight = (document.body.offsetHeight+1000)+'px';
         }
         else
         {
            var pageWidth  = '100%';
            var pageHeight = '100%';
         }


         // Set the shader to cover the entire page and make it visible.

         dark.style.opacity         = opaque;
         dark.style.MozOpacity      = opaque;
         dark.style.filter          = 'alpha(opacity='+opacity+')';
         dark.style.zIndex          = zindex;
         dark.style.backgroundColor = bgcolor;
         dark.style.width           = pageWidth;
         dark.style.height          = pageHeight;
         dark.style.display         = 'block';
      }

      else
         dark.style.display='none';
   }



   /* "Please Wait" message with clock */

   me.grayOutMessage = function(vis)
   {
      var msg = document.getElementById('messageScreenObject');

      if(!msg)
      {
         var tbody = document.getElementsByTagName("body")[0];

         var tnode = document.createElement('div');

         tnode.style.width           = '230px';
         tnode.style.height          = '40px';
         tnode.style.position        = 'absolute';
         tnode.style.top             = '50%';
         tnode.style.left            = '50%';
         tnode.style.zIndex          = '5500';
         tnode.style.margin          = '-50px 0 0 -100px';
         tnode.style.backgroundColor = '#ffffff';
         tnode.style.display         = 'none';
         tnode.innerHTML             = '<img src="waitClock.gif"/> &nbsp; Loading.  Please wait ... ';
         tnode.id                    = 'messageScreenObject';

         tbody.appendChild(tnode);

         msg = document.getElementById('messageScreenObject');
      }

      if(vis)
         msg.style.display = 'block';
      else
         msg.style.display = 'none';
   }
}

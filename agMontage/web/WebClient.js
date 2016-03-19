function WebClient(server, port)
{
   var me = this;

   me.debug = false;

   me.msgCallbacks = [];



   // Start up the connection and set up
   // callbacks for open, close, and 
   // message receive.

   me.host   = "ws://" + server + ":" + port + "/ws";

   if(me.debug)
      console.log("DEBUG> host: " + me.host);   
    
   me.socket = new WebSocket(me.host);

   if(me.debug)
      console.log("DEBUG> socket status: " + me.socket.readyState);   
    
   if(me.socket)
   {
      // Open callback

      me.socket.onopen = function()
      {
         if(me.debug)
            console.log("DEBUG>  Connection opened ...");
      }


      // Receive message callback

      me.socket.onmessage = function(msg)
      {
          me.receive(msg.data);
      }


      // Close callback

      me.socket.onclose = function()
      {
        if(me.debug)
           console.log("DEBUG>  The connection has been closed.");
      }
   }
   else
      if(me.debug)
         console.log("DEBUG>  Invalid socket.");



   // SEND to server

   me.send = function(text)
   {
      // Wait until the state of the socket is not ready and send the message when it is...
      me.waitForSocketConnection(function(){

         me.socket.send(text);

         if(me.debug)
            console.log("Message [" + text + "] sent");
      });
   }


   // Make the function wait until the connection is made

   me.waitForSocketConnection = function(callback)
   {
      if(me.debug)
         console.log("Wait 5 milliseconds for socket to be ready ...");

      setTimeout(

         function() 
	 {
            if (me.socket.readyState === 1)
	    {
               if(callback != null)
                  callback();

               return;

            } else 
               me.waitForSocketConnection(callback);

         }, 5); // wait 5 millisecond for the connection...
}


   // RECEIVE from server

   me.receive = function(msg)
   {
      if(me.debug)
         console.log("DEBUG>  Receiving: " + msg);

      for(i=0; i<me.msgCallbacks.length; ++i)
         me.msgCallbacks[i](msg);
   } 


   me.addMsgCallback = function(method)
   {
      me.msgCallbacks.push(method);
   }
}

"""steam_client directory

This directory contains all code that facilitates a connection between us and a steam server. As far as Steam's servers are concerned, we are a Steam Client. 

This requires a few parts: First, we need to get a list of servers we can connect to, so we need a http client to connect to a static address and get all available servers. then, to communicate with the servers, we need a websocket connection. Then we need a means to send them messages and get the responses. 

Messages are compiled protobuf files. we do not use all of them, but we do require a great deal of them. 
"""
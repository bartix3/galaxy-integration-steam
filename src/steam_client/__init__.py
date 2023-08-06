"""Steam_Network directory (and corresponding __init__.py)

This module contains all the related Model-View-Client code that handles interfacing the GOG Galaxy Client Plugin and Steam's Servers.

For the most part, the view and model do not store any information - instead, they are given information from the controller and return any and all information \
that the controller requires. Note that the information may not be used by the controller, but passed-through to the model or view. In other cases, the model \
or view may provide information that is necessary in case an action fails and needs to be repeated with different information. The controller is responsible \
for persisting this data, not the model or view. There are a few exceptions, however. Steam can send us server-side messages that we did not ask for, but \
will use in future calls. This information is stored in a dedicated "cache" that exists alongside the model. 

Stated another way, the model has two means of obtaining the data the controller requests: look it up in the cache and return it, or request it directly from steam. \
If possible, data will be cached so it does not need to be queried constantly, then updated as new information becomes available. 

The controller must be able to replay a certain message 

"""
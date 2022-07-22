name: Genevieve Sanders
uni: gs2908

NOTE: test.txt is integrated into information below + supplemented with pictures in subfolder implementation_pics.

DESCRIPTION:
The following application (consisting of main ChatApp.py, client.py, and server.py) implements a simple UDP chatroom.

To initialize the underlying server, one uses command $ python3 ChatApp.py -s [port number]. For example, in the example photo server.png, the  port number chosen was 1024. If given a viable port number, the script will print a statement indicating the server is being initialize; otherwise, it will ask for a viable port number.

Now, let’s create 3 users (each in their own terminal window) - @gs2908, @milliethebear, and @funuser3. If we create users in this order, we will be notified that the client table is updated with each subsequent registered user, and each user will receive an opening message of
	“>>> [Welcome @[USER], You are registered.]”
At this point, we see user @gs2908 call function
	“>>> peers”
which prints a local dictionary record of all known clients with a list of their IP, port number, and online status (as a boolean.) (This trajectory and that of the following paragraph can be seen in client-gs2908.png.)

Next, user @gs2908 sends herself a message saying “hey me!” She receives this message (with preceding code PM to indicate it is a private message) as well as a notification that her self-message was successfully received. She then uses the command structure
	 “>>> send [USER] [message]”
to ask @milliethebear “what's it like to always be dancing?” She is notified that this message was received and gets a PM message back from Millie before then receiving a Channel Message from @funuser3. (The other side of all of these interactions can be seen in the other client-[USERNAME] photos.)

@gs2908 uses command
	“>>>send_all [message]”
to send a group chat message before logging off temporarily using
	“>>>dereg [USERNAME]”.
She receives a notification she is offline, and when she logs back on using
	“>>>reg [USERNAME]”
she is notified that she has some unread messages - two channel messages from @milliethebear and @funuser3, and one PM from @funuser3 (all with time stamps.) Such offline messages are stored in username-labeled text files created with new user registration. @gs2908 sends back a group message (which is notified to be successfully received by the Server) and receives one more group message before using Command+C to initiate a error-handled silent leave as seen below.
	“^C >>> [Keyboard Interrupt detected; silent leave initiated]”
	“Client @gs2908 has exited.”


IMPLEMENTED SERVER/CLIENT INTIALIZATION COMMANDS:
	python3 ChatApp.py -s (port number)
	OR
	python3 ChatApp.py -c (name, server_ip, server_port, client_port)

IMPLEMENTED CLIENT COMMANDS:
	dereg (username)
	reg (username)
	send_all (message)
	send (target_user) (message)
	peers
		*** bonus function to see local client table!
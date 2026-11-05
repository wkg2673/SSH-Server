import paramiko
import socket
import threading

# Set the login credentials
USERNAME = "user123"
PASSWORD = "password123"

# Store successful login credentials
successful_logins = []


class SSHServerHandler(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_auth_password(self, username, password):
        """Authenticate users."""
        global successful_logins
        if username == USERNAME and password == PASSWORD:
            print(f"Successful login: {username}")
            successful_logins.append((username, password))
            return paramiko.AUTH_SUCCESSFUL
        else:
            print(f"Failed login attempt: {username}")
            return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "password"

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_pty_request(self, channel, term, width, height, pixelwidth, pixelheight):
        """Allow PTY requests."""
        return True

    def check_shell_request(self, channel):
        """Handle shell requests."""
        return True


def start_ssh_server(host="0.0.0.0", port=2222):
    """Start the SSH server."""
    # Generate server keys
    key = paramiko.RSAKey.generate(2048)

    # Set up socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(5)
    print(f"SSH Server running on {host}:{port}")

    while True:
        client, addr = sock.accept()
        print(f"Connection attempt from {addr}")

        try:
            transport = paramiko.Transport(client)
            transport.add_server_key(key)
            server = SSHServerHandler()

            try:
                transport.start_server(server=server)
            except paramiko.SSHException as e:
                print(f"SSH negotiation failed: {e}")
                client.close()
                continue

            # Accept the connection
            chan = transport.accept(20)  # Wait for a channel
            if chan is None:
                print("No channel received. Connection closed.")
                client.close()
                continue

            # Send the welcome message
            chan.send("Welcome to the SSH server!\n")

            # Enter an interactive session if the client requested a shell
            while True:
                try:
                    # Read incoming data (if any)
                    data = chan.recv(1024)
                    if not data:
                        # If no data, break the loop (client has closed the connection)
                        break

                    # Echo the received data back to the client (basic interaction)
                    chan.send(f"You said: {data.decode()}\n")
                except Exception as e:
                    print(f"Error while handling channel: {e}")
                    break

            chan.close()
        except Exception as e:
            print(f"Error during connection handling: {e}")
        finally:
            client.close()


if __name__ == "__main__":
    try:
        start_ssh_server(host="127.0.0.1", port=2222)  # Use a non-privileged port
    except KeyboardInterrupt:
        print("\nSSH Server shutting down.")
    except Exception as e:
        print(f"Failed to start SSH server: {e}")

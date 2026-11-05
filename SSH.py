import paramiko
import socket
import threading

# login credentials
USERNAME = "user123"
PASSWORD = "password123"
# Store credentials
successful_logins = []

class SSHServerHandler(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_auth_password(self, username, password):
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
        return True
    def check_shell_request(self, channel):
        return True

def start_ssh_server(host="0.0.0.0", port=2222):
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
            # Accept connection
            chan = transport.accept(20)
            if chan is None:
                print("No channel received. Connection closed.")
                client.close()
                continue
            # Send welcome message
            chan.send("Welcome to the SSH server!\n")
            # Enter interactive session if client wants shell
            while True:
                try:
                    # Read data
                    data = chan.recv(1024)
                    if not data:
                        # If no data, break loop
                        break
                    # Echo recevied data back to client
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
        start_ssh_server(host="127.0.0.1", port=2222)
    except KeyboardInterrupt:
        print("\nSSH Server shutting down.")
    except Exception as e:
        print(f"Failed to start SSH server: {e}")

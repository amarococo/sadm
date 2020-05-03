#! /opt/prologin/venv/bin/python

"""Long-running program to setup and cleanup user homes as NBD mounts.

Communicates with lightdm-prologin-greeter through a UNIX socket. Meant to run
on user machines, as root. Meant to be run through systemd socket activation:
this script does not create the socket, it reuses FD 3 from systemd activation.

This server is not asynchronous by design, as a single peer (LightDM) should
connect anyway.

Security shall be enforced through socket ACLs, that is, only lightdm shall get
read and write access to the pipe.

Protocol description (text, UTF-8, line-based):
[ greeter ]                      [ prologind ]
  setup <username>\n    ------->
                        <-------   message <progress text>\n
                        <-------   (other 'message' lines)
                        <-------   success\n
                                     OR
                        <-------   error <reason>\n

  cleanup <username>\n  ------->
                        <-------   success\n
                                     OR
                        <-------   error <reason>\n
"""

from socketserver import TCPServer, StreamRequestHandler
import logging
import os.path
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable

import prologin.hfs.client
import prologin.log
import prologin.presenced.client

prologin.log.setup_logging('prologind')


def get_home_dir(username: str):
    return f'/home/{username}'


def get_block_device(username):
    return '/dev/nbd0'


def invoke_redirect_std(cmd, **kwargs):
    return subprocess.check_call(
        cmd, stdout=sys.stderr, stderr=sys.stderr, **kwargs
    )


def message(message: str):
    return f"message {message.splitlines()[0]}"


def error(reason: str):
    return f"error {reason.splitlines()[0]}"


def success():
    return "success"


def setup(username: str) -> Iterable[str]:
    # Already mounted?
    if os.path.ismount(get_home_dir(username)):
        yield success()
        return

    # System users not controlled by udb are unrestricted:
    if not prologin.presenced.client.is_prologin_user(username):
        yield success()
        return

    yield message("checking user…")

    # Request the login to presenced and presencesync.
    failure_reason = prologin.presenced.client.connect().request_login(
        username
    )
    if failure_reason is not None:
        # Login is forbidden by presenced.
        yield error(f"login forbidden: {failure_reason}")
        return

    yield message("requesting HOME migration…")

    # Request HOME directory migration and wait for it.
    hfs = prologin.hfs.client.connect()
    try:
        hostname = socket.gethostname()
        if hostname.endswith('.prolo'):
            hostname = hostname[: -len('.prolo')]
        else:
            logging.warning('hostname does not end with .prolo: %s', hostname)
        host, port = hfs.get_hfs(username, hostname)
    except Exception as err:
        logging.exception("error requesting HOME migration for %s", username)
        return error(str(err))

    yield message("setting up the block device…")

    home_dir = get_home_dir(username)
    # Create the HOME mount point if needed. There is no need to fix
    # permissions: this is only a mount point.
    Path(home_dir).mkdir(exist_ok=True)

    # Get a block device for the HOME mount point and mount it.
    #
    # Containers used for testing do not have the netlink nbd family available
    # (see genl-ctrl-list(8)), therefore fallback to using ioctl with the
    # -nonetlink option. Exercise for the reader: figure how to enable the ndb
    # netlink family in a systemd-nspawn container.
    #
    # TODO: experiment with '-block-size' values and compare performance
    block_device = get_block_device(username)
    if invoke_redirect_std(
        [
            '/usr/sbin/nbd-client',
            '-nonetlink',
            '-name',
            username,
            host,
            str(port),
            block_device,
        ]
    ):
        yield error("cannot get the home directory block device")
        return

    yield message("mounting home directory…")

    if invoke_redirect_std(['/bin/mount', block_device, home_dir]):
        yield error("cannot mount the home directory")
        return

    yield success()


def cleanup(username: str) -> Iterable[str]:
    # System users not controlled by udb are unrestricted:
    if not prologin.presenced.client.is_prologin_user(username):
        return

    # Make sure the user has nothing else running
    try:
        invoke_redirect_std(['/usr/bin/pkill', '-9', '-u', username])
    except subprocess.CalledProcessError as err:
        # "No processes matched" errors are fine.
        if err.returncode != 1:
            logging.exception("error pkill'ing user '%s' processes", username)
            # Try un-mounting anyway.

    # Unmount /home/user.
    time.sleep(2)
    invoke_redirect_std(['/bin/umount', '-R', get_home_dir(username)])

    # Stop the nbd client.
    block_device = get_block_device(username)

    # Due to a bug somewhere between nbd-client and the kernel, detaching with
    # -nonetlink fails with: 'Invalid nbd device target /dev/nbd0'.
    try:
        invoke_redirect_std(['/usr/sbin/nbd-client', '-d', block_device])
    except subprocess.CalledProcessError:
        # Here's the workaround: only try without -nonetlink if the above
        # command fails.
        invoke_redirect_std(
            ['/usr/sbin/nbd-client', '-d', '-nonetlink', block_device]
        )

    yield success()


def handle_command(line: str) -> Iterable[str]:
    cmd, rest = line.rstrip().split(' ', 1)

    if cmd == 'setup':
        return setup(rest)
    elif cmd == 'cleanup':
        return cleanup(rest)

    logging.error("received unknown command '%s'", cmd)


class Handler(StreamRequestHandler):
    def read_line(self) -> str:
        return self.rfile.readline().strip().decode()

    def write_line(self, line: str):
        self.wfile.write((line + '\n').encode())
        self.wfile.flush()

    def handle(self):
        while True:
            try:
                line = self.read_line()
            except UnicodeDecodeError:
                continue
            except:
                return

            try:
                for result in handle_command(line):
                    self.write_line(result)
            except Exception as err:
                self.write_line(error(str(err)))


class Server(TCPServer):
    SYSTEMD_FIRST_SOCKET_FD = 3

    def __init__(self, server_address, handler_cls):
        # systemd activation is performing the bind + activate.
        super().__init__(server_address, handler_cls, bind_and_activate=False)
        # Override socket with systemd's.
        self.socket = socket.fromfd(
            self.SYSTEMD_FIRST_SOCKET_FD, self.address_family, self.socket_type
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = Server(("", 0), Handler)
    server.serve_forever()

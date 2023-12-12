import logging
import time
from enum import Enum, auto
from threading import Thread

from irc.bot import SingleServerIRCBot
from rich.logging import RichHandler

from TwitchChannelPointsMiner.classes.Settings import Events, Settings
from TwitchChannelPointsMiner.constants import IRC, IRC_PORT

logger = logging.getLogger(__name__)


FORMAT = "%(message)s"
logging.basicConfig(level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

logger = logging.getLogger("rich")


class ChatPresence(Enum):
    """Enum representing the presence options for a chat.

    Options:
    - ALWAYS: The chat is always present.
    - NEVER: The chat is never present.
    - ONLINE: The chat is present when the user is online.
    - OFFLINE: The chat is present when the user is offline.
    """

    ALWAYS = auto()
    NEVER = auto()
    ONLINE = auto()
    OFFLINE = auto()

    def __str__(self):
        """Returns a string representation of the Chat object."""
        return self.name


class ClientIRC(SingleServerIRCBot):
    def __init__(self, username, token, channel):
        self.token = token
        self.channel = "#" + channel
        self.__active = False

        super().__init__([(IRC, IRC_PORT)], username, username)

    def on_welcome(self, client, event):
        client.join(self.channel)

    def start(self):
        self.__active = True
        self._connect()
        while self.__active:
            try:
                self.reactor.process_once(timeout=0.2)
                time.sleep(0.01)
            except Exception as e:
                logger.error(f"Exception raised: {e}. Thread is active: {self.__active}")

    def die(self, msg="Bye, cruel world!"):
        self.connection.disconnect(msg)
        self.__active = False

    """
    def on_join(self, connection, event):
        logger.info(f"Event: {event}", extra={"emoji": ":speech_balloon:"})
    """

    # """
    def on_pubmsg(self, connection, event):
        msg = event.arguments[0]
        mention = None

        if Settings.disable_at_in_nickname is True:
            mention = f"{self._nickname.lower()}"
        else:
            mention = f"@{self._nickname.lower()}"

        # also self._realname
        # if msg.startswith(f"@{self._nickname}"):
        if mention is not None and mention in msg.lower():
            # nickname!username@nickname.tmi.twitch.tv
            nick = event.source.split("!", 1)[0]
            # chan = event.target

            logger.info(
                f"{nick} at {self.channel} wrote: {msg}",
                extra={"emoji": ":speech_balloon:", "event": Events.CHAT_MENTION},
            )

    # """


class ThreadChat(Thread):
    def __deepcopy__(self, memo):
        """Create a shallow copy of the ThreadChat object."""
        return None

    def __init__(self, username, token, channel):
        super().__init__()

        self.username = username
        self.token = token
        self.channel = channel

        self.chat_irc = None

    def run(self):
        self.chat_irc = ClientIRC(self.username, self.token, self.channel)
        logger.info(f"Join IRC Chat: {self.channel}", extra={"emoji": ":speech_balloon:"})
        self.chat_irc.start()

    def stop(self):
        if self.chat_irc is not None:
            logger.info(f"Leave IRC Chat: {self.channel}", extra={"emoji": ":speech_balloon:"})
            self.chat_irc.die()

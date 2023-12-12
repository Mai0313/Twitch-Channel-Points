import logging
import os
import platform

import autorootcwd
from colorama import Fore
from omegaconf import OmegaConf
from pydantic import BaseModel

from TwitchChannelPointsMiner import TwitchChannelPointsMiner
from TwitchChannelPointsMiner.classes.Chat import ChatPresence
from TwitchChannelPointsMiner.classes.Discord import Discord
from TwitchChannelPointsMiner.classes.entities.Bet import (
    BetSettings,
    Condition,
    DelayMode,
    FilterCondition,
    OutcomeKeys,
    Strategy,
)
from TwitchChannelPointsMiner.classes.entities.Streamer import Streamer, StreamerSettings
from TwitchChannelPointsMiner.classes.Matrix import Matrix
from TwitchChannelPointsMiner.classes.Pushover import Pushover
from TwitchChannelPointsMiner.classes.Settings import Events, FollowersOrder, Priority
from TwitchChannelPointsMiner.classes.Telegram import Telegram
from TwitchChannelPointsMiner.logger import ColorPalette, LoggerSettings


def check_platform():
    """This function will check if you are using Windows or Linux/MacOS."""
    if platform.system() == "Windows":
        emoji = False
    else:
        emoji = True
    return emoji


def get_user_secret():
    """This function will load username/password automatically from .env or secret.yaml file."""
    secret_path = "./configs/secret.yaml"
    if os.path.exists(secret_path):
        secret = OmegaConf.load(secret_path)
        username, password = secret.username, secret.password
    else:
        from dotenv import load_dotenv

        load_dotenv()
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
    return username, password


config = OmegaConf.load("./configs/setting.yaml")


class TwitchMiner(BaseModel):
    username: str
    password: str

    def get_miner(self):
        return TwitchChannelPointsMiner(
            username=self.username,
            password=self.password,
            claim_drops_startup=config.claim_drops_startup,
            priority=[  # Custom priority in this case for example:
                Priority.STREAK,  # - We want first of all to catch all watch streak from all streamers
                Priority.DROPS,  # - When we don't have anymore watch streak to catch, wait until all drops are collected over the streamers
                Priority.ORDER,  # - When we have all of the drops claimed and no watch-streak available, use the order priority (POINTS_ASCENDING, POINTS_DESCEDING)
            ],
            logger_settings=LoggerSettings(
                save=config.save,
                console_level=logging.INFO,  # Level of logs - use logging.DEBUG for more info
                console_username=False,  # Adds a username to every console log line if True. Also adds it to Telegram, Discord, etc. Useful when you have several accounts
                auto_clear=True,  # Create a file rotation handler with interval = 1D and backupCount = 7 if True (default)
                time_zone="",  # Set a specific time zone for console and file loggers. Use tz database names. Example: "America/Denver"
                file_level=logging.INFO,  # Level of logs - If you think the log file it's too big, use logging.INFO
                emoji=check_platform(),
                less=config.less,
                colored=config.colored,
                color_palette=ColorPalette(  # You can also create a custom palette color (for the common message).
                    STREAMER_online="GREEN",  # Don't worry about lower/upper case. The script will parse all the values.
                    streamer_offline="red",  # Read more in README.md
                    BET_wiN=Fore.MAGENTA,  # Color allowed are: [BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET].
                ),
                telegram=Telegram(
                    chat_id=config.telegram.chat_id,
                    token=config.telegram.token,
                    events=[
                        Events.STREAMER_ONLINE,
                        Events.STREAMER_OFFLINE,
                        Events.BET_LOSE,
                        Events.CHAT_MENTION,
                    ],  # Only these events will be sent to the chat
                    disable_notification=config.telegram.disable_notification,
                ),
                discord=Discord(
                    webhook_api=config.discord.webhook_api,
                    events=[
                        Events.STREAMER_ONLINE,
                        Events.STREAMER_OFFLINE,
                        Events.BET_LOSE,
                        Events.CHAT_MENTION,
                    ],  # Only these events will be sent to the chat
                ),
                matrix=Matrix(
                    username="twitch_miner",  # Matrix username (without homeserver)
                    password="...",  # Matrix password
                    homeserver="matrix.org",  # Matrix homeserver
                    room_id="...",  # Room ID
                    events=[
                        Events.STREAMER_ONLINE,
                        Events.STREAMER_OFFLINE,
                        Events.BET_LOSE,
                    ],  # Only these events will be sent to the chat
                ),
                pushover=Pushover(
                    userkey="YOUR-ACCOUNT-TOKEN",  # Login to https://pushover.net/, the user token is on the main page.
                    token="YOUR-APPLICATION-TOKEN",  # Create a application on the website, and use the token shown in your application.
                    priority=0,  # Read more about priority here: https://pushover.net/api#priority
                    sound="pushover",  # A list of sounds can be found here: https://pushover.net/api#sounds
                    events=[
                        Events.CHAT_MENTION,
                        Events.DROP_CLAIM,
                    ],  # Only these events will be sent.
                ),
            ),
            streamer_settings=StreamerSettings(
                make_predictions=config.bet_strategy.make_predictions,
                follow_raid=config.bet_strategy.follow_raid,
                claim_drops=config.bet_strategy.claim_drops,
                claim_moments=True,  # If set to True, https://help.twitch.tv/s/article/moments will be claimed when available
                watch_streak=config.bet_strategy.watch_streak,
                chat=ChatPresence.ONLINE,
                bet=BetSettings(
                    strategy=Strategy.SMART,
                    percentage=config.bet_strategy.percentage,
                    percentage_gap=config.bet_strategy.percentage_gap,
                    max_points=config.bet_strategy.max_points,
                    stealth_mode=config.bet_strategy.stealth_mode,
                    delay_mode=DelayMode.FROM_END,  # When placing a bet, we will wait until `delay` seconds before the end of the timer
                    delay=config.bet_strategy.delay,
                    minimum_points=config.bet_strategy.minimum_points,
                    filter_condition=FilterCondition(
                        by=OutcomeKeys.TOTAL_USERS,  # Where apply the filter. Allowed [PERCENTAGE_USERS, ODDS_PERCENTAGE, ODDS, TOP_POINTS, TOTAL_USERS, TOTAL_POINTS]
                        where=Condition.LTE,  # 'by' must be [GT, LT, GTE, LTE] than value
                        value=800,
                    ),
                ),
            ),
        )


# You can customize the settings for each streamer. If not settings were provided, the script would use the streamer_settings from TwitchChannelPointsMiner.
# If no streamer_settings are provided in TwitchChannelPointsMiner the script will use default settings.
# The streamers array can be a String -> username or Streamer instance.

# The settings priority are: settings in mine function, settings in TwitchChannelPointsMiner instance, default settings.
# For example, if in the mine function you don't provide any value for 'make_prediction' but you have set it on TwitchChannelPointsMiner instance, the script will take the value from here.
# If you haven't set any value even in the instance the default one will be used

# twitch_miner.analytics(host="127.0.0.1", port=5000, refresh=5, days_ago=7)   # Start the Analytics web-server

if __name__ == "__main__":
    username, password = get_user_secret()
    twitch_miner = TwitchMiner(username=username, password=password)
    twitch_miner = twitch_miner.get_miner()
    twitch_miner.mine(
        [],  # Array of streamers (order = priority)
        followers=True,  # Automatic download the list of your followers
        followers_order=FollowersOrder.ASC,  # Sort the followers list by follow date. ASC or DESC
    )
    # twitch_miner.mine(
    #     [
    #         Streamer(
    #             "streamer-username01",
    #             settings=StreamerSettings(
    #                 make_predictions=True,
    #                 follow_raid=False,
    #                 claim_drops=True,
    #                 watch_streak=True,
    #                 bet=BetSettings(
    #                     strategy=Strategy.SMART,
    #                     percentage=5,
    #                     stealth_mode=True,
    #                     percentage_gap=20,
    #                     max_points=234,
    #                     filter_condition=FilterCondition(
    #                         by=OutcomeKeys.TOTAL_USERS, where=Condition.LTE, value=800
    #                     ),
    #                 ),
    #             ),
    #         ),
    #         Streamer(
    #             "streamer-username02",
    #             settings=StreamerSettings(
    #                 make_predictions=False,
    #                 follow_raid=True,
    #                 claim_drops=False,
    #                 bet=BetSettings(
    #                     strategy=Strategy.PERCENTAGE,
    #                     percentage=5,
    #                     stealth_mode=False,
    #                     percentage_gap=20,
    #                     max_points=1234,
    #                     filter_condition=FilterCondition(
    #                         by=OutcomeKeys.TOTAL_POINTS, where=Condition.GTE, value=250
    #                     ),
    #                 ),
    #             ),
    #         ),
    #         Streamer(
    #             "streamer-username03",
    #             settings=StreamerSettings(
    #                 make_predictions=True,
    #                 follow_raid=False,
    #                 watch_streak=True,
    #                 bet=BetSettings(
    #                     strategy=Strategy.SMART,
    #                     percentage=5,
    #                     stealth_mode=False,
    #                     percentage_gap=30,
    #                     max_points=50000,
    #                     filter_condition=FilterCondition(
    #                         by=OutcomeKeys.ODDS, where=Condition.LT, value=300
    #                     ),
    #                 ),
    #             ),
    #         ),
    #         Streamer(
    #             "streamer-username04",
    #             settings=StreamerSettings(make_predictions=False, follow_raid=True, watch_streak=True),
    #         ),
    #         Streamer(
    #             "streamer-username05",
    #             settings=StreamerSettings(
    #                 make_predictions=True,
    #                 follow_raid=True,
    #                 claim_drops=True,
    #                 watch_streak=True,
    #                 bet=BetSettings(
    #                     strategy=Strategy.HIGH_ODDS,
    #                     percentage=7,
    #                     stealth_mode=True,
    #                     percentage_gap=20,
    #                     max_points=90,
    #                     filter_condition=FilterCondition(
    #                         by=OutcomeKeys.PERCENTAGE_USERS, where=Condition.GTE, value=300
    #                     ),
    #                 ),
    #             ),
    #         ),
    #         Streamer("streamer-username06"),
    #         Streamer("streamer-username07"),
    #         Streamer("streamer-username08"),
    #         "streamer-username09",
    #         "streamer-username10",
    #         "streamer-username11",
    #     ],  # Array of streamers (order = priority)
    #     followers=False,  # Automatic download the list of your followers
    #     followers_order=FollowersOrder.ASC,  # Sort the followers list by follow date. ASC or DESC
    # )

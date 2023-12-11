import logging
import platform

import autorootcwd
from colorama import Fore
from omegaconf import OmegaConf

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


config = OmegaConf.load("./configs/setting.yaml")
secret = OmegaConf.load("./configs/secret.yaml")

twitch_miner = TwitchChannelPointsMiner(
    username=secret.username,
    password=secret.password,
    claim_drops_startup=config.claim_drops_startup,
    priority=[  # Custom priority in this case for example:
        Priority.STREAK,  # - We want first of all to catch all watch streak from all streamers
        Priority.DROPS,  # - When we don't have anymore watch streak to catch, wait until all drops are collected over the streamers
        Priority.ORDER,  # - When we have all of the drops claimed and no watch-streak available, use the order priority (POINTS_ASCENDING, POINTS_DESCEDING)
    ],
    logger_settings=LoggerSettings(
        save=config.save,
        console_level=logging.INFO,  # Level of logs - use logging.DEBUG for more info
        file_level=logging.DEBUG,  # Level of logs - If you think the log file it's too big, use logging.INFO
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
            events=[Events.STREAMER_ONLINE, Events.STREAMER_OFFLINE, "BET_LOSE"],
            disable_notification=config.telegram.disable_notification,
        ),
        discord=Discord(
            webhook_api=config.discord.webhook_api,
            events=[
                Events.STREAMER_ONLINE,
                Events.STREAMER_OFFLINE,
                Events.BET_LOSE,
            ],  # Only these events will be sent to the chat
        ),
    ),
    streamer_settings=StreamerSettings(
        make_predictions=config.bet_strategy.make_predictions,
        follow_raid=config.bet_strategy.follow_raid,
        claim_drops=config.bet_strategy.claim_drops,
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

twitch_miner.mine(
    [],  # Array of streamers (order = priority)
    followers=True,  # Automatic download the list of your followers
    followers_order=FollowersOrder.ASC,  # Sort the followers list by follow date. ASC or DESC
)

from datetime import datetime, timedelta

from module.guild.assets import GUILD_RED_DOT
from module.guild.base import GUILD_RECORD
from module.guild.lobby import GuildLobby
from module.guild.logistics import GuildLogistics
from module.guild.operations import GuildOperations
from module.logger import logger
from module.ui.assets import CAMPAIGN_CHECK, EVENT_CHECK, SP_CHECK
from module.ui.ui import page_guild


class RewardGuild(GuildLobby, GuildLogistics, GuildOperations):
    def guild_run(self, logistics=True, operations=True):
        """
        Execute logistics and operations actions
        if enabled by arguments

        Pages:
            in: Any page
            out: page_main
        """
        if not logistics and not operations:
            return False

        # By default, going to page_guild always
        # opens into lobby
        self.ui_ensure(page_guild)

        # Wait for possible report to be displayed
        # after entering page_guild
        # If already in page guild but not lobby,
        # checked on next reward loop
        self.guild_lobby()

        if logistics:
            self.guild_logistics()

        if operations:
            self.guild_operations()

        self.ui_goto_main()

        return True

    def handle_guild(self):
        """
        ALAS handler function for guild reward loop

        Returns:
            bool: If executed
        """
        # Both disabled, do not run
        if not self.config.ENABLE_GUILD_LOGISTICS and not self.config.ENABLE_GUILD_OPERATIONS:
            return False

        # Default before checking
        do_logistics = False
        do_operations = False

        # Check circumstances of handle_guild
        # - Coming from campaign, event or sp due to guild popup
        # - Reward Loop, enter if interval elapsed or iff red_dot present
        appear = [self.appear(check, offset=(20, 20)) for check in [CAMPAIGN_CHECK, EVENT_CHECK, SP_CHECK]]
        if any(appear):
            do_logistics = self.config.ENABLE_GUILD_LOGISTICS
            do_operations = self.config.ENABLE_GUILD_OPERATIONS
        else:
            now = datetime.now()
            guild_record = datetime.strptime(self.config.config.get(*GUILD_RECORD), self.config.TIME_FORMAT)
            update = guild_record + timedelta(seconds=self.guild_interval)
            attr = f'{GUILD_RECORD[0]}_{GUILD_RECORD[1]}'
            logger.attr(f'{attr}', f'Record time: {guild_record}')
            logger.attr(f'{attr}', f'Next update: {update}')
            if now > update or self.appear(GUILD_RED_DOT, offset=(30, 30)):
                do_logistics = self.config.ENABLE_GUILD_LOGISTICS
                do_operations = self.config.ENABLE_GUILD_OPERATIONS

        if not self.guild_run(logistics=do_logistics, operations=do_operations):
            return False

        self.guild_interval_reset()
        self.config.record_save(option=('RewardRecord', 'guild'))

        return True

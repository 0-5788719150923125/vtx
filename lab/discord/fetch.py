import os
import shutil
import sys

sys.path.append("/src")

from common import config, get_past_datetime

root_dir = "/lab/discord"


# Fetch messages from Discord, by using Discord Chat Exporter
def main():
    # By default, use the bot's token
    discord_token = os.environ["DISCORDTOKEN"]

    # If a self token is specific, use that
    if "use_self_token" in config["discord"]:
        if config["discord"]["use_self_token"] == True:
            discord_token = os.environ["DISCORDSELFTOKEN"]

    # Ensure directory has been created
    if not os.path.exists(f"{root_dir}/source"):
        os.makedirs(f"{root_dir}/source")

    # Export direct messages
    if config["discord"]["export_dms"] == True:
        command = f'dotnet /usr/share/dce/DiscordChatExporter.Cli.dll exportdm -t "{discord_token}" -o "{root_dir}/source/dm/%c - %C (%G).json" -f "JSON" --fuck-russia'
        os.system(command)

    # For every server listed in config, iterate over options, and download messages
    for server in config["discord"]["servers"]:
        print("exporting " + str(server))

        s = config["discord"]["servers"].get(server, {})
        command = f'dotnet /usr/share/dce/DiscordChatExporter.Cli.dll exportguild --guild "{str(server)}" -t "{discord_token}" -o "{root_dir}/source/%g/%c - %C (%G).json" -f "JSON" --include-threads "all" --fuck-russia'

        if s.get("skip", False):
            continue
        if "before" in s:
            command = command + ' --before "' + s["before"] + '"'
        if "after" in s:
            command = command + ' --after "' + s["after"] + '"'
        if "past" in s:
            d = get_past_datetime(s["past"])
            command = command + f' --after "{str(d)}"'

        shutil.rmtree(f"{root_dir}/source/{server}", ignore_errors=True)

        os.system(command)


if __name__ == "__main__":
    main()

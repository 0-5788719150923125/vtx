import os
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
        command = f'dotnet /usr/share/dce/DiscordChatExporter.Cli.dll exportdm --fuck-russia -t "{discord_token}" -o "{root_dir}/source/dm-%c.json" -f "JSON"'
        os.system(command)

    # For every server listed in config, iterate over options, and download messages
    for server in config["discord"]["servers"]:
        print("exporting " + str(server))

        skip = False
        s = config["discord"]["servers"][server]
        command = f'dotnet /usr/share/dce/DiscordChatExporter.Cli.dll exportguild --include-threads --include-archived-threads --fuck-russia --guild "{str(server)}" -t "{discord_token}" -o "{root_dir}/source/g-%g-%c.json" -f "JSON"'
        if s:
            if "skip" in s:
                skip = s.get("skip", False)
            if skip == True:
                continue
            if "before" in s:
                command = command + ' --before "' + s["before"] + '"'
            if "after" in s:
                command = command + ' --after "' + s["after"] + '"'
            if "past" in s:
                d = get_past_datetime(s["past"])
                command = command + f' --after "{str(d)}"'
        for filename in os.listdir(f"{root_dir}/source"):
            if filename.startswith(f"g-{str(server)}"):
                os.remove(os.path.join(f"{root_dir}/source", filename))
        os.system(command)


if __name__ == "__main__":
    main()

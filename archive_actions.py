import CHApproverBot

for log in CHApproverBot.praw.models.util.stream_generator(CHApproverBot.SUBREDDIT.mod.log, attribute_name = "id"):
    if str(log.mod) != "AutoModerator":
        print(log.id)
        CHApproverBot.blacklist(log.id)
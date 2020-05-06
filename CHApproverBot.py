import logging
import pickle
import praw
import json
import os

logging.basicConfig( 
    format = "[%(asctime)s] %(message)s", 
    level = logging.INFO,
    handlers=[
        logging.FileHandler("approval_log.log"),
        logging.StreamHandler()
    ])

CONFIG_FILE = "config.json"
BLACKLIST_FILE = "approver_blacklist.csv"
APPROVED_FILE = "approved_users.pickle"

with open(CONFIG_FILE, "r") as f:
    CONFIG = json.load(f)

if not os.path.exists(APPROVED_FILE):
    with open(APPROVED_FILE, "wb") as f:
        pickle.dump(set(), f)

REDDIT = praw.Reddit(**CONFIG["redditapi"])
SUBREDDIT = REDDIT.subreddit(CONFIG["subreddit"])

def blacklist(action_id):
    with open(BLACKLIST_FILE, "a") as f:
        f.write(action_id + "\n")

def action_blacklisted(action_id):
    if not os.path.exists(BLACKLIST_FILE):
        return False

    with open(BLACKLIST_FILE, "r") as f:
        links = f.read().splitlines()
    return action_id in links

def get_mods():
    return [str(i) for i in SUBREDDIT.moderator()] + ["AutoModerator"]

def get_approved():
    with open(APPROVED_FILE, "rb") as f:
        try:
            return pickle.load(f)
        except EOFError:
            return set()

def user_approved(user):
    return user in get_approved()
    
def append_approved(user):
    #cant do this without assigning a variable because I/O errors
    approved = get_approved()
    approved.add(user)
    with open(APPROVED_FILE, "wb") as f:
        pickle.dump(approved, f)

def remove_approved(user):
    approved = get_approved()
    approved.remove(user)
    with open(APPROVED_FILE, "wb") as f:
        pickle.dump(approved, f)

def main():
    while True:
        for log in praw.models.util.stream_generator(SUBREDDIT.mod.log, attribute_name = "id", pause_after=-1):
            if log is None:
                break

            if log.action == "approvelink" and not action_blacklisted(log.id):
                if str(log.mod) != "AutoModerator":
                    blacklist(log.id)
                
                subj = CONFIG["subject"].replace("<>", str(SUBREDDIT))
                submission = REDDIT.submission(url = "https://reddit.com" + log.target_permalink)

                if str(submission.author) not in get_mods() and not user_approved(str(submission.author)):
                    submission.author.message(
                        subj, 
                        CONFIG["message"].replace("<>", "https://redd.it/" + submission.id), 
                        from_subreddit = SUBREDDIT
                    )
                    append_approved(str(submission.author))

                    for conv in SUBREDDIT.modmail.conversations():
                       if conv.subject.startswith(subj[:23]) or conv.subject == "you are an approved user":
                           conv.archive()

                    try:
                        SUBREDDIT.flair.set(submission.author, text = ":approved: Approved user", flair_template_id="2b56a12c-7c2f-11ea-9666-0e72ae1d5f77")
                    except:
                        logging.info("Couldn't get the flair ID")

                    logging.info("Added user /u/%s for the submission https://redd.it/%s" % (submission.author, submission.id))

            elif log.action == "removelink" and not action_blacklisted(log.id) and str(log.mod) == "AutoModerator":
                blacklist(log.id)
                submission = REDDIT.submission(url = "https://reddit.com" + log.target_permalink)
                if not action_blacklisted(submission.id):
                    blacklist(submission.id)
                    submission.mod.approve()
                    logging.info("Approved submission %s from approved user /u/%s" % (submission.id, submission.author))
        
        for comment in SUBREDDIT.stream.comments(pause_after=-1):
            if comment is None:
                break
            
            if "!removeapproved" in comment.body.lower() and comment.author in get_mods() and not action_blacklisted(comment.id):
                blacklist(comment.id)

                if user_approved(str(comment.submission.author)):
                    remove_approved(str(comment.submission.author))
                    reply = comment.reply("/u/%s has been removed as an approved submitter from /r/%s for posting '[%s](%s)'. \n\n%s" % (
                        comment.submission.author, str(SUBREDDIT), comment.submission.title, "https://redd.it/" + comment.submission.title, CONFIG["tail"].replace("<>", str(SUBREDDIT))
                    ))
                    reply.mod.distinguish()
                    reply.mod.approve()

                    SUBREDDIT.flair.delete(comment.submission.author)

                    logging.info("Removed user /u/%s for the submission https://redd.it/%s" % (comment.submission.author, comment.submission.id))


if __name__ == "__main__":
    with open("pid.json", "w") as f:
        json.dump(os.getpid(), f)
    
    logging.info("=== RESTARTED ===")
    main()

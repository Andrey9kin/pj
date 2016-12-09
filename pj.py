from boto3 import Session
from contextlib import closing
import os
import sys
import jenkins
import logging
from tempfile import gettempdir
import argparse
from github import Github

jenkins_url = "http://code.praqma.net/ci"
job_name = "2git-release"

# Return (debug, url, job, output_dir, voice, account)
def parse_args(args):
    parser = argparse.ArgumentParser(description='Read build result from Jenkins, extract commit info (assuming GitHub) and generate message using Amazon Polly')
    parser.add_argument("-d", "--debug", action="store_true",
                        help="print debug info")    
    parser.add_argument("-u", "--url", default=jenkins_url,
                        help="Jenkins URL, {} if not specified".format(jenkins_url))
    parser.add_argument("-j", "--job", default=job_name,
                        help="Job name, {} if not specified".format(job_name))
    parser.add_argument("-o", "--output", default="",
                        help="output dir, tmp dir will be created if not specified")
    parser.add_argument("-v", "--voice", default="Joanna",
                        help="voice id to use, Joanna if not defined")
    parser.add_argument("-a", "--account", default="", required=True,
                        help="AWS credentials to use, i.e. section from ~/.aws/credentials file")
    parsed = parser.parse_args()
    return (parsed.debug, parsed.url, parsed.job, parsed.output, parsed.voice, parsed.account)

# Return (repo, sha1, build number, result)
def get_info_from_jenkins(jenkins_url, job_name):
    logging.info("Connect to Jenkins at {}".format(jenkins_url))
    repo = ""
    sha1 = ""
    server = jenkins.Jenkins(jenkins_url)
    logging.info("Get latest build for the job {} from Jenkins server {}".format(job_name, jenkins_url))
    last_build_number = server.get_job_info(job_name)['lastCompletedBuild']['number']
    build_info = server.get_job_info(job_name, last_build_number)

    for action in build_info['lastCompletedBuild']['actions']:
        if 'remoteUrls' in action:
            repo = action['remoteUrls'][0]
            sha1 = action['lastBuiltRevision']['SHA1']

    if repo == "" and sha1 == "":
        raise LookupError("Can not get repo and sha1 info for job {}".format(job_name))

    logging.info("Jenkins job {} with the build number {} built repo {} sha1 {}".format(job_name, last_build_number, repo, sha1))
    return (repo, sha1, last_build_number, build_info['lastCompletedBuild']['result'])

# Return (github_user, github_repo)
def get_username_and_repo(repo_url):
    logging.debug("Get username and repo from {}".format(repo_url))
    github_user = repo_url.split('/')[-2]
    github_repo = (repo_url.split('/')[-1]).replace('.git','')
    logging.debug("Extracted {} and {}".format(github_user, github_repo))
    return (github_user, github_repo)

# Return (name, commit message(only first line))
def get_name_and_commit_msg_from_github(username, repo, sha1):
    logging.debug("Get author name and commmit message from sha1 {} in repo {} of user {}".format(username, repo, sha1))
    github = Github()
    github_repo = github.get_repo("{}/{}".format(username,repo))
    commit = github_repo.get_git_commit(sha1)
    return (commit.author.name, (commit.message).split('\n', 1)[0])

# Retun path to file
def get_audio_from_polly(account, text, output_dir="", voice="Joanna"):
    # Create a client using the credentials and region defined in the [adminuser]
    # section of the AWS credentials file (~/.aws/credentials).
    output = os.path.join(output_dir if  output_dir != "" else gettempdir(), "message.mp3")
    logging.info("Login to AWS")
    session = Session(profile_name=account)
    polly = session.client("polly")

    # Request speech synthesis
    logging.info("Request audio for {}".format(text))
    response = polly.synthesize_speech(Text=text,
                                       OutputFormat="mp3",
                                       VoiceId=voice)

    # Access the audio stream from the response
    if "AudioStream" in response:
        # Note: Closing the stream is important as the service throttles on the
        # number of parallel connections. Here we are using contextlib.closing to
        # ensure the close method of the stream object will be called automatically
        # at the end of the with statement's scope.
        with closing(response["AudioStream"]) as stream:
            # Open a file for writing the output as a binary stream
            logging.debug("Write received audio to {}".format(output))
            with open(output, "wb") as file:
                file.write(stream.read())
    else:
        raise KeyError("No AudioStream found in response: {}".format(repsonse))
    return output

# Returns message
def get_message(name, commit_message, build_number, job, result):
    message = "Message for user {}! Message for user {}! Your commit with the commit message - {},".format(name, name, commit_message)
    if result == "FAILURE":
        message += " broke the build number - {}, for the job - {}. Go and fix it! God dammit!".format(build_number, job)
    elif result == "SUCCESS":
        message += " was succesfully built by the job - {}, build number - {}. Well done! Keep it up!".format(job, build_number)
    elif result == "ABORT":
        message += " was building by the job - {}, with the build number - {}. But! Someone aborted it!".format(job, build_number)
    elif result == "UNSTABLE":
        message += " didn't pass tests in the build number - {}, for the job - {}. Go and fix it! God dammit!".format(build_number, job)
    else:
        message += "... hold on! Something happend but I have no idea what! Please check logs!"
    return message

def main(argv):
    try:
        debug, url, job, output_dir, voice, account = parse_args(argv)
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        repo_url, sha1, build_number, result = get_info_from_jenkins(url, job)
        username, repo = get_username_and_repo(repo_url)
        logging.info("Extracted github user name - {}".format(username))
        logging.info("Extracted github repo name - {}".format(repo))
        name, commit_message = get_name_and_commit_msg_from_github(username, repo, sha1)
        logging.info("Extracted name - {}".format(name))
        logging.info("Extracted commit message - {}".format(commit_message))
        text = get_message(name, commit_message, build_number, job, result)
        output = get_audio_from_polly(account, text, output_dir, voice)
        logging.info("Message saved to file {}".format(output))
    except Exception as error:
        logging.error(error)
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv[1:])

# -*- coding: UTF-8 -*-

import json
import urlparse
import sh

from ...lib.ci_exception import CiException
from ...lib.gravity import Dependency
from ...lib.module_arguments import IncorrectParameterError
from ...lib import utils
from ..reporter import ReportObserver, Reporter
from . import git_vcs

__all__ = [
    "GerritMainVcs",
    "GerritSubmitVcs"
]


class GerritVcs(git_vcs.GitVcs):
    """
    This class contains encapsulates Gerrit VCS functions
    """

    def __init__(self, *args, **kwargs):
        super(GerritVcs, self).__init__(*args, **kwargs)
        self.reporter = None

        if not self.settings.repo.startswith("ssh://"):
            raise IncorrectParameterError("Right now Gerrit builds are only available via SSH access")

        parsed_repo = urlparse.urlparse(self.settings.repo)
        self.hostname = parsed_repo.hostname
        self.ssh = sh.ssh.bake(parsed_repo.username+"@"+self.hostname, p=parsed_repo.port)
        self.commit_id = None
        self.review = None
        self.review_version = None

    def run_ssh_command(self, line, stdin=None, stdout=None):
        try:
            return self.ssh(line, _in=stdin, _out=stdout)
        except sh.ErrorReturnCode as e:
            text = "Got exit code " + unicode(e.exit_code) + \
                   " while executing the following command:\n" + unicode(e.full_cmd)
            if e.stderr:
                text += utils.trim_and_convert_to_unicode(e.stderr) + "\n"
            raise CiException(text)


class GerritMainVcs(ReportObserver, GerritVcs, git_vcs.GitMainVcs):
    reporter_factory = Dependency(Reporter)

    def code_review(self):
        # Gerrit code review system is Gerrit itself
        if not self.settings.refspec:
            raise IncorrectParameterError("Please pass 'refs/changes/...' to --git-refspec parameter")

        if self.settings.checkout_id:
            raise IncorrectParameterError("Please use --git-refspec instead of commit ID")

        self.reporter = self.reporter_factory()
        self.reporter.subscribe(self)
        return self

    def update_review_version(self):
        refspec = self.settings.refspec
        if refspec.startswith("refs/"):
            refspec = refspec[5:]
        if not self.review:
            self.review = refspec.split("/")[2]
        if not self.review_version:
            self.review_version = refspec.split("/")[3]

    def get_review_link(self):
        self.update_review_version()
        return "https://" + self.hostname + "/#/c/" + self.review + "/"

    def _get_patch_set_description(self, reference):
        request = "gerrit query --current-patch-set --format json " + reference
        response = unicode(self.run_ssh_command(request))

        # response is expected to consist of two json objects: patch set description and query summary
        # JSONDecoder.raw_decode() decodes first json object and ignores all that follows
        try:
            decoder = json.JSONDecoder()
            result = decoder.raw_decode(response)
            return result[0]
        except (KeyError, ValueError):
            text = "Error parsing gerrit server response. Full response is the following:\n"
            text += response
            raise CiException(text)

    def is_latest_version(self):
        self.update_review_version()
        review_description = self._get_patch_set_description("change:" + self.review)
        latest_version = int(review_description["currentPatchSet"]["number"])

        if int(self.review_version) == latest_version:
            return True

        text = "Current review version is " + self.review_version + \
               ", while latest review version is already " + self.review_latest_version
        self.out.log(text)

        return False

    def calculate_file_diff(self):
        review_description = self._get_patch_set_description("commit:" + self.commit_id)
        target_branch = review_description["branch"]
        reference_commit = self.repo.git.merge_base(target_branch, self.commit_id)
        return self._diff_against_reference_commit(unicode(reference_commit))

    def code_report_to_review(self, report):
        # git show returns string, each file separated by \n,
        # first line consists of commit id and commit comment, so it's skipped
        commit_files = self.repo.git.show("--name-only", "--oneline", self.commit_id).split('\n')[1:]
        stdin = {'comments': {}}
        text = "gerrit review " + self.commit_id + ' --json '
        for path, issues in report.iteritems():
            if path in commit_files:
                stdin['comments'].update({path: issues})
        self.run_ssh_command(text, json.dumps(stdin))

    def report_start(self, report_text):
        text = "gerrit review --message '" + report_text + "' " + self.commit_id
        self.run_ssh_command(text)

    def report_result(self, result, report_text=None, no_vote=False):
        if result:
            vote = "--label Verified=1 "
        else:
            vote = "--label Verified=-1 "

        text = "gerrit review "
        if not no_vote:
            text += vote
        if report_text:
            text += "--message '" + report_text + "' "

        text += self.commit_id
        self.run_ssh_command(text)

    def prepare_repository(self):
        super(GerritMainVcs, self).prepare_repository()
        self.commit_id = unicode(self.repo.head.commit)


class GerritSubmitVcs(GerritVcs, git_vcs.GitSubmitVcs):
    def submit_new_change(self, description, file_list, review=False, edit_only=False):
        change = self.git_commit_locally(description, file_list, edit_only=edit_only)

        self.repo.remotes.origin.push(progress=self.logger, refspec="HEAD:refs/for/" + self.refspec)

        if not review:
            text = "gerrit review --submit --code-review +2 --label Verified=1 --message 'This is an automatic vote' "
            text += change
            self.run_ssh_command(text)

        return change

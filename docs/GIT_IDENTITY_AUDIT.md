# Git identity audit and correction

Date: 2026-10-16. Requested by the owner after noticing an incorrect author on the first V2 commit.

## Evidence and cause

- The authenticated GitHub account was **HY-D1**, ID 93563405, with push permission.
- The inherited global `user.name`/`user.email` entries in `~/.gitconfig` were `Hermes Agent` / `hermes@local.dev`. Neither repository had a local override, and no GIT_AUTHOR/GIT_COMMITTER environment override was set.
- The initial commit `2a29a94db5a1edd6755852eeaf79979685e62a0d` consequently recorded that name/email for both author and committer. The GitHub API returned null linked accounts. The agent did not verify commit identity before creating it; this was an operational error.
- The source or time of the earlier global configuration change is unverified. This audit does not establish that Hermes ran or changed the project.
- GitHub associates command-line commits using the commit email, separately from authentication for pushing: [GitHub commit-email documentation](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address) and [attribution troubleshooting](https://docs.github.com/en/enterprise-cloud%40latest/pull-requests/how-tos/commit-changes/troubleshooting-commits) (checked 2026-10-16).

## Authorized correction

The owner instructed: use Hanyu Dai or HY-D1 and remove the other identity. Global Git identity and local overrides for both project repositories were set to:

```text
user.name = Hanyu Dai
user.email = 93563405+HY-D1@users.noreply.github.com
```

The email was verified against an existing GitHub commit linked to HY-D1, not guessed from an unrelated account. It is GitHub's account-specific privacy address.

The owner-authored portfolio branch was checked against its exact remote head before rewriting the single agent-created commit. A local recovery ref (`refs/backup/portfolio-v2-author-fix-20261016`) preserves the old commit. The replacement commit is `7b96a39e873165ebd236576b57846dff7eb03f04`; author and committer are Hanyu Dai and the GitHub API links both to **HY-D1**. Comparing the two commit trees produced no differences. Only that known branch head was updated with an explicit expected-SHA lease; main and existing source edits were preserved.

This corrects branch history and future commits. The old SHA can remain accessible through GitHub's cached history, PR events or the previously shared URL; no deletion of unrelated collaborators' history or account data was performed.

## Verification commands

```bash
git show --no-patch --format=fuller HEAD
git config --show-origin --show-scope --get-regexp '^user\.(name|email)$'
git log origin/main..HEAD --format='%h %an | %cn'
gh api repos/HY-D1/amazon-sales-analytics/commits/7b96a39e873165ebd236576b57846dff7eb03f04 --jq '{author_name:.commit.author.name,committer_name:.commit.committer.name,linked_author:.author.login,linked_committer:.committer.login}'
```

Actual API result: author/committer name **Hanyu Dai**; linked author/committer **HY-D1**. Global and both repository-local values match. Future publication should verify identity before committing.

#!/bin/sh
# Amend a commit's author only if it was committed under an address GitHub
# cannot recognise. Safe to re-run: already-correct commits are left alone.
#
# Identities deliberately NOT touched:
#   41898282+github-actions[bot]@...   nightly workflow commits
#   89400000+Nortaq-PlayNexus@...     older account id, still linked
# Re-attributing the bot's commits to the human would be a false record.
EMAIL="$(git log -1 --format=%ae)"
case "$EMAIL" in
  natha@natha-m2|opencode@localhost|dev@nexusx.local|aurora@example.com)
    echo "      reauthoring $EMAIL"
    git commit --amend --no-edit --reset-author --quiet
    ;;
esac

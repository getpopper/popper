#!/bin/bash
set -ex

source common-setup.sh

init_test
popper init archive_pipe
git config user.email "testuser@example.com"
git config user.name "Test User"
echo "echo \"Today's date is: $(date +"%Y%m%d-%H%M%S")\"" >> pipelines/archive_pipe/post-run.sh
popper metadata --add title='Popper test archive'
popper metadata --add author1='Test Author, testauthor@gmail.com, popper'
popper metadata --add abstract='A short description of the article'
popper metadata --add keywords='comma, separated, keywords'
git remote add origin https://github.com/systemslab/popper-test.git
git add . && git commit -m "Add metadata"
cat .popper.yml
#popper archive --service zenodo
#popper archive --service zenodo --publish
#popper archive --service zenodo --show-doi

popper metadata --add categories='1656'
git add . && git commit -m "Modify metadata"
cat .popper.yml
#popper archive --service figshare
#popper archive --service figshare --publish
#popper archive --service figshare --show-doi

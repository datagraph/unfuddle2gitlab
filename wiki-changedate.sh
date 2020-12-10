set -e
REPOOLD="$PWD/notebooks.wiki"
REPONEW="$PWD/notebooks-timed.wiki"
rm -rf $REPONEW
mkdir $REPONEW
cd $REPONEW
git init
cd $REPOOLD

ii=0
for githash in `git log --reverse|grep "commit "|cut -d" " -f2` ;
do
    if [ $ii -gt 10000 ]
    then
        exit;
    else
        let "ii+=1"
        echo loop $ii
    fi

    echo $githash
    git checkout $githash
    name=`git log --format='%an' $githash|head -1`
    mail=`git log --format='%ae' $githash|head -1`
    subj=`git log --format='%s' $githash|head -1`
    patchfile=`git format-patch -1`
    cd $REPONEW
    git am < $REPOOLD/$patchfile
    date=`git show|grep "+updated-at: #"|cut -d'#' -f2;`
    if [ -z "$date" ]
    then
      echo "no commit date found, maybe a attachment"
    else
      echo $date
      GIT_COMMITTER_DATE="$date" git commit --amend --no-edit --date="$date"
    fi
    cd $REPOOLD
done


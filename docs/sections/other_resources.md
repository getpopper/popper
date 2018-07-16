# Other Resources

## Self-paced Tutorial

We have a hands-on, self-paced tutorial available 
[here](https://popperized.github.io/swc-lesson).

## CI Setup

By following a convention for structuring the files of a project, an 
experimentation pipeline execution and validation can be automated 
without the need for manual intervention. In addition to this, the 
status of a pipeline (integrity over time) can be tracked by a 
[continuous integration (CI) 
service](https://en.wikipedia.org/wiki/Comparison_of_continuous_integration_software). 
In this section we describe how to generate configuration files and 
how to setup a CI service so that it continously validate the 
integrity of a pipeline.

The `popper` command includes `ci` subcommand that can be executed to 
generate configuration files for multiple CI systems. The syntax of 
this command is the following:

```bash
popper ci --service <name>
```

Where `<name>` is the name of CI system (see `popper ci --help` to get 
a list of supported systems). In the following, we show how to link 
github with some of the supported CI systems. In order to do so, we 
first need to create a repository on github and upload our commits:

```bash
# set the new remote
git remote add origin <your-github-repo-url>

# verify the remote URL
git remote -v

# push changes in your local repository up to github
git push -u origin master
```

### TravisCI

For this, we need an account at [Travis CI](http://travis-ci.org). 
Assuming our Popperized repository is already on GitHub, we can enable 
it on TravisCI so that it is continuously validated (see 
[here](https://docs.travis-ci.com/user/getting-started/) for a guide). 
Once the project is registered on Travis, we proceed to generate a 
`.travis.yml` file:

```bash
cd my-popper-repo/
popper ci --service travis
```

And commit the file:

```bash
git add .travis.yml
git commit -m 'Adds TravisCI config file'
```

We then can trigger an execution by pushing to GitHub:

```bash
git push
```

After this, one go to the TravisCI website to see your pipelines being 
executed. Every new change committed to a public repository will 
trigger an execution of your pipelines. To avoid triggering an 
execution for a commit, include a line with `[skip ci]` as part of the 
commit message.

> **NOTE**: TravisCI has a limit of 2 hours, after which the test is 
> terminated and failed.

### CircleCI

For [CircleCI](https://circleci.com/), the procedure is similar to 
what we do for TravisCI (see above):

 1. Sign in to CircleCI using your github account and enable your 
    repository.

 2. Generate config files and add them to the repo:

    ```bash
    cd my-popper-repo/
    popper ci --service circle
    git add .circleci
    git commit -m 'Adds CircleCI config files'
    git push
    ```

### Jenkins

For [Jenkins](https://jenkinsci.org), generating a `Jenkinsfile` is 
done in a similar way:

```bash
cd my-popper-repo/
popper ci --service jenkins
git add Jenkinsfile
git commit -m 'Adds Jenkinsfile'
git push
```

Jenkins is a self-hosted service and needs to be properly configured 
in order to be able to read a github project with a `Jenkinsfile` in 
it. The easiest way to add a new project is to use the [Blue Ocean 
UI](https://jenkins.io/projects/blueocean/). A step-by-step guide on 
how to create a new project using the Blue Ocean UI can be found 
[here](https://jenkins.io/doc/book/blueocean/creating-pipelines/). In 
particular, the `New Pipeline from a Single Repository` has to be 
selected (as opposed to `Auto-discover Pipelines`).

As part of our efforts, we provide a ready-to-use Docker image for 
Jenkins with all the required dependencies (see below) for an example 
of how to use it. We also host an instance of this image at 
<http://ci.falsifiable.us> and allow anyone to make use of this 
Jenkins server.

#### Jenkins Docker Image

We have created an image with all the plugins necessary to 
automatically validate pipelines. To launch an instance of this Docker 
image server:

```bash
docker run -d --name=jenkins \
  -p 8080:8080 \
  -v jenkins_home:/var/jenkins_home \
  falsifiable/jenkins
```

The above launches a Jenkins server that can be accessed on port 
`8080` of the machine where this command was launched (e.g. 
`localhost:8080` if you did this on your machine).

For more info on how to use this image, take a look at the [official 
documentation](https://github.com/jenkinsci/docker/blob/master/README.md) 
for this image.

#### [`ci.falsifiable.us`](http://ci.falsifiable.us)

Create an account by clicking the `Sign Up` link on the top right 
corner. After this, you will be able to access the server. Follow the 
steps outlined above to generate a `Jenkinsfile` using the `popper` 
command. Alternatively, create this file manually with the following 
contents:

```
stage ('Popper') {
  node {
    sh "git clone --recursive https://github.com/systemslab/popper /tmp/popper"
    sh "export PATH=$PATH:/tmp/popper/cli/bin"
    sh "export PYTHONUNBUFFERED=1"
  }
}
```

Then, follow [this step-by-step 
guide](https://jenkins.io/doc/book/blueocean/creating-pipelines/) on 
how to create a new project using the Blue Ocean UI.

## Automated Artifact Evaluation

**TODO**

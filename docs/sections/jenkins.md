# Self-hosting Jenkins

We describe how to deploy Jenkins using Docker, and how to make use of 
the Jenkins instance running at <http://ci.falsifiable.us>. For more 
on how to make add CI configuration files to a repository using 
Popper, see 
[here](cli_features.html#continuously-validating-a-pipeline). For a 
detailed description on the CI features available to Popper, see 
[here](ci_features.html).

## Jenkins Docker Image

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

## [`ci.falsifiable.us`](http://ci.falsifiable.us)

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

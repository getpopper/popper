# Jenkins Docker Image

We have created an image with all the plugins necessary to 
automatically validate Popper pipelines. To launch an instance of this 
Docker image server:

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

# [`ci.falsifiable.us`](http://ci.falsifiable.us)

To make use of our server, please first send a message to 
<ivo@cs.ucsc.edu> to request an account. After an account is created, 
you will be able to access the server. Follow the steps [outlined 
here](http://popper.readthedocs.io/en/latest/ci/popperci.html#jenkins) 
to add a `Jenkinsfile` to your project. Alternatively, create this 
file manually with the following contents:

```
stage ('Popper') {
  node {
    sh "curl -O https://raw.githubusercontent.com/systemslab/popper/master/popper/_check/check.py"
    sh "chmod 755 check.py"
    sh "./check.py"
  }
}
```

Then, follow [this step-by-step 
guide](https://jenkins.io/doc/book/blueocean/creating-pipelines/) on 
how to create a new project using the Blue Ocean UI.

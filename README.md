## Report contributions

| Section                             | Member in charge |
|-------------------------------------|------------------|
| Preamble                            | Ronja Meier      |
| Design decisions, technology choice | Philipp Gorke    |
| Evaluation, Analysis                |                  |
| Conclusion                          |                  |
| Theory Questions                    | Samuel Lechner   |

## Setup guide

### Pre-requisites:

We have used Windows machines, so we can't guarantee that the following instructions will work on other operating systems.
Either way, execute the steps below in the given order.

### Localstack
We will run localstack in a docker environment. To install docker, follow the instructions [here](https://docs.docker.com/get-docker/).
To run the docker container, execute the following command:
```bash
docker-compose up -d
```
**By the way**: _If you want to shut down the container afterward, use ````docker-compose down````_.

### Amazon CDK

If you don't have Node.js installed by now, you can download it [here](https://nodejs.org/en/download/package-manager).
```bash
npm install -g aws-cdk-local aws-cdk@2.166.0
```
Please ensure that the version indeed matches _2.166.0_. We don't install the latest version because we found out there's a bug which is not yet fixed.
```bash
cdklocal --version
```

Next, we will navigate to our cdk project.
```bash
cd cdk
```
Install the required dependencies for the CDK project. I recommend opening the project in an IDE like PyCharm, as it will provide you with a venv where pip is already installed. Have a look the [CDK readme file](cdk/README.md) for more details.
```bash
pip install -r requirements.txt
```
In the cdk directory, simply run the following commands to deploy the stack:
```bash
cdklocal bootstrap
```
```bash
cdklocal deploy
```
Aaaand we're done! The stack should be deployed by now :)

### Dashbaord

Once it is up and running, you can inspect it by checking out the [localstack web dashboard](https://app.localstack.cloud/).
This requires you to create an account first (it's free, you don't have to choose a subscription plan at all).
Credentials don't matter as the application only accesses your local docker container running on ```https://localhost.localstack.cloud:4566```.

By the way: The localstack pro key is used in the ```docker-compose.yml```, so you don't have to worry about that.

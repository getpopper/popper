import os
import subprocess

from popper import utils as pu
from popper import scm
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner
from popper.runner_host import DockerRunner as HostDockerRunner
from popper.runner_host import HostRunner


class SlurmRunner(StepRunner):

    spawned_jobs = set()

    def __init__(self, config):
        super(SlurmRunner, self).__init__(config)

    def __exit__(self, exc_type, exc, traceback):
        SlurmRunner.spawned_jobs = set()

    def generate_script(self, cmd, job_id):
        with open(f"{job_id}.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write(cmd)

    def submit_batch_job(self, cmd, step):
        job_id = pu.sanitized_name(step['name'], self.config.wid)
        self.generate_script(cmd, job_id)

        sbatch_cmd = "sbatch --wait "
        sbatch_cmd += f"--job-name {job_id} "

        if hasattr(self.config, 'resman_options'):
            options = self.config.resman_options
            if options.get(step['name']):
                step_slurm_config = options[step['name']]
                for config_key, config_val in step_slurm_config.items():
                    if isinstance(config_val, bool):
                        if len(config_key) == 1:
                            sbatch_cmd += f"-{config_key} "
                        else:
                            sbatch_cmd += f"--{config_key} "
                    else:
                        if len(config_key) == 1:
                            sbatch_cmd += f"-{config_key} {config_val} "
                        else:
                            sbatch_cmd += f"--{config_key} {config_val} "

        sbatch_cmd += f"{job_id}.sh"
        log.debug(sbatch_cmd)

        SlurmRunner.spawned_jobs.add(job_id)
        ecode = pu.exec_cmd(sbatch_cmd.split(" "))
        SlurmRunner.spawned_jobs.remove(job_id)
        return ecode

    def cancel_job(self):
        for job_id in SlurmRunner.spawned_jobs:
            log.info(f'Cancelling job {job_id}')
            pu.exec_cmd(["scancel", "--name", job_id])


class DockerRunner(SlurmRunner, HostDockerRunner):
    def __init__(self, config):
        super(DockerRunner, self).__init__(config)

    def run(self, step):
        """Execute the given step in docker."""
        # generate cid
        cid = pu.sanitized_name(step['name'], self.config.wid)
        step['cmd_list'] = []

        # prepare image build artifacts
        build, img, dockerfile = HostDockerRunner.get_build_info(
            step, self.config.workspace_dir, self.config.workspace_sha)

        if build:
            DockerRunner.docker_build(step, img, dockerfile, self.config.dry_run)
        elif not self.config.skip_pull and not step.get('skip_pull', False):
            DockerRunner.docker_pull(step, img, self.config.dry_run)

        # remove container if it exists
        DockerRunner.docker_rm(step, cid, self.config.dry_run)
        
        # create container
        DockerRunner.docker_create(step, img, cid, self.config)
        
        if self.config.dry_run:
            return 0

        HostDockerRunner.spawned_containers.append(cid)
        DockerRunner.docker_start(step, cid, self.config.dry_run)
        return self.run_script(step)

    def run_script(self, step):
        final_cmd = "\n".join(step['cmd_list'])
        return self.submit_batch_job(final_cmd, step)

    @staticmethod
    def docker_create(step, img, cid, config):
        msg = f'{img} {step.get("runs", "")} {step.get("args", "")}'
        log.info(f'[{step["name"]}] docker create {msg}')
        
        engine_config = HostDockerRunner.get_engine_config(step, img, cid, config)
        engine_config.pop('detach')
        docker_cmd = "docker create "
        docker_cmd += f"--name {engine_config.pop('name')} "
        docker_cmd += f"--workdir {engine_config.pop('working_dir')} "

        if engine_config.get('entrypoint', None):
            docker_cmd += f"--entrypoint '{' '.join(engine_config.pop('entrypoint'))}' "

        # append the vol and envs
        for vol in engine_config.pop('volumes'):
            docker_cmd += f"-v {vol} "
        for env_key, env_val in engine_config.pop('environment').items():
            docker_cmd += f"-e {env_key}={env_val} "

        image = engine_config.pop('image')

        if engine_config.get('command', None):
            command = ' '.join(engine_config.pop('command'))
        else:
            command = ' '

        for config_key, config_val in engine_config.items():
            if not config_val:
                continue

            if isinstance(config_val, bool):
                if len(config_key) == 1:
                    docker_cmd += f"-{config_key} "
                else:
                    docker_cmd += f"--{config_key} "
            elif isinstance(config_val, list):
                for item in config_val:
                    if len(config_key) == 1:
                        docker_cmd += f"-{config_key} {item} "
                    else:
                        docker_cmd += f"--{config_key} {item} "
            else:
                if len(config_key) == 1:
                    docker_cmd += f"-{config_key} {config_val} "
                else:
                    docker_cmd += f"--{config_key} {config_val} "
        
        # append the image and the commands
        docker_cmd += f"{image} {command}"
        step['cmd_list'].append(docker_cmd)

    @staticmethod
    def docker_start(step, cid, dry_run):
        log.info(f'[{step["name"]}] docker start')
        if dry_run:
            return
        docker_cmd = f"docker start --attach {cid}"
        step['cmd_list'].append(docker_cmd)

    @staticmethod
    def docker_pull(step, img, dry_run):
        log.info(f'[{step["name"]}] docker pull {img}')
        if dry_run:
            return
        docker_cmd = f"docker pull {img}"
        step['cmd_list'].append(docker_cmd)

    @staticmethod
    def docker_build(step, tag, path, dry_run):
        log.info(f'[{step["name"]}] docker build -t {tag} {path}')
        if dry_run:
            return
        docker_cmd = f"docker build {tag} {path}"
        step['cmd_list'].append(docker_cmd)

    @staticmethod
    def docker_rm(step, cid, dry_run):
        log.info(f'[{step["name"]}] docker rm {cid}')
        if dry_run:
            return
        docker_cmd = f"docker rm -f {cid} || true"
        step['cmd_list'].append(docker_cmd)

    def stop_running_tasks(self):
        for cid in HostDockerRunner.spawned_containers:
            log.info(f'Stopping container {cid}')
            pu.exec_cmd(["docker", "stop", cid])
        self.cancel_job()

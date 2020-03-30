import os
import time
import tempfile
import subprocess
import threading

import sh

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
    
    def _stream_output(self, out_file):
        self.tail_proc_pid = set()
        pu.exec_cmd(["tail", "-f", out_file], spawned_processes=self.tail_proc_pid)

    def start_output_stream(self, out_file):
        self.stream_thread = threading.Thread(
            target=self._stream_output, args=(out_file,))
        self.stream_thread.start()

    def stop_output_stream(self):
        proc = list(self.tail_proc_pid)[0]
        proc.kill()
        self.stream_thread.join()
    
    @staticmethod
    def generate_script(cmd, job_name, job_script):
        with open(job_script, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(cmd)

    @staticmethod
    def touch_log_files(out_file, err_file):
        if os.path.exists(out_file):
            os.remove(out_file)

        if os.path.exists(err_file):
            os.remove(err_file)

        sh.touch(out_file)
        sh.touch(err_file)

    def submit_batch_job(self, cmd, step):
        job_name = pu.sanitized_name(step['name'], self.config.wid)
        temp_dir = "/tmp/popper/slurm/"
        os.makedirs(temp_dir, exist_ok=True)

        job_script = os.path.join(temp_dir, f"{job_name}.sh")
        out_file = os.path.join(temp_dir, f"{job_name}.out")
        err_file = os.path.join(temp_dir, f"{job_name}.err")

        SlurmRunner.touch_log_files(out_file, err_file)
        SlurmRunner.generate_script(cmd, job_name, job_script)

        sbatch_cmd = "sbatch --wait "
        sbatch_cmd += f"--job-name {job_name} "
        sbatch_cmd += f"--output {out_file} "
        sbatch_cmd += f"--error {err_file} "

        for k, v in self.config.resman_options.get(step['name'], {}).items():
            sbatch_cmd += "-" if len(k) == 1 else "--"
            if isinstance(v, bool):
                sbatch_cmd += f"{k} "
            else:
                sbatch_cmd += f"{k} {v} "

        sbatch_cmd += job_script
        log.debug(sbatch_cmd)

        SlurmRunner.spawned_jobs.add(job_name)

        # start a tail process on the output file
        self.start_output_stream(out_file)

        # submit the job and wait, then parse the job_id
        ecode, output = pu.exec_cmd(sbatch_cmd.split(" "), stream=False)
        job_id = int(output.split(" ")[-1].strip("\n"))
        
        # kill the tail process
        self.stop_output_stream()

        SlurmRunner.spawned_jobs.remove(job_name)
        return ecode

    def cancel_job(self):
        for job_name in SlurmRunner.spawned_jobs:
            log.info(f'Cancelling job {job_name}')
            pu.exec_cmd(["scancel", "--name", job_name])


class DockerRunner(SlurmRunner):
    spawned_containers = set()

    def __init__(self, config):
        super(DockerRunner, self).__init__(config)

    def __exit__(self, exc_type, exc, traceback):
        spawned_containers = set()

    def run(self, step):
        """Execute the given step in docker."""
        # generate cid
        cid = pu.sanitized_name(step['name'], self.config.wid)
        step['cmd_list'] = []

        # prepare image build artifacts
        build, img, dockerfile = HostDockerRunner.get_build_info(
            step, self.config.workspace_dir, self.config.workspace_sha)

        if build:
            DockerRunner.docker_build(
                step, img, dockerfile, self.config.dry_run)
        elif not self.config.skip_pull and not step.get('skip_pull', False):
            DockerRunner.docker_pull(step, img, self.config.dry_run)

        # remove container if it exists
        DockerRunner.docker_rm(step, cid, self.config.dry_run)

        # create container
        DockerRunner.docker_create(step, img, cid, self.config)

        if self.config.dry_run:
            return 0

        DockerRunner.spawned_containers.add(cid)
        DockerRunner.docker_start(step, cid, self.config.dry_run)
        ecode = self.run_script(step)
        DockerRunner.spawned_containers.remove(cid)
        return ecode

    def run_script(self, step):
        step['cmd_list'] = list(map(lambda x: 'srun ' + x, step['cmd_list']))
        final_cmd = "\n".join(step['cmd_list'])
        return self.submit_batch_job(final_cmd, step)

    @staticmethod
    def docker_create(step, img, cid, config):
        msg = f'{img} {step.get("runs", "")} {step.get("args", "")}'
        log.info(f'[{step["name"]}] docker create {msg}')

        engine_config = HostDockerRunner.get_engine_config(
            step, img, cid, config)
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

        for k, v in engine_config.items():
            if not v:
                continue
            if isinstance(v, bool):
                docker_cmd += "-" if len(k) == 1 else "--"
                docker_cmd += f"{k} "
            elif isinstance(v, list):
                for item in v:
                    docker_cmd += "-" if len(k) == 1 else "--"
                    docker_cmd += f"{k} {item} "
            else:
                docker_cmd += "-" if len(k) == 1 else "--"
                docker_cmd += f"{k} {v} "

        # append the image and the commands
        docker_cmd += f"{image} {command} > /dev/null"
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
        docker_cmd = f"docker pull {img} > /dev/null"
        step['cmd_list'].append(docker_cmd)

    @staticmethod
    def docker_build(step, tag, path, dry_run):
        log.info(f'[{step["name"]}] docker build -t {tag} {path}')
        if dry_run:
            return
        docker_cmd = f"docker build {tag} {path} > /dev/null"
        step['cmd_list'].append(docker_cmd)

    @staticmethod
    def docker_rm(step, cid, dry_run):
        if dry_run:
            return
        docker_cmd = f"docker rm -f {cid} || true > /dev/null"
        step['cmd_list'].append(docker_cmd)

    def stop_running_tasks(self):
        for cid in DockerRunner.spawned_containers:
            log.info(f'Stopping container {cid}')
            pu.exec_cmd(["docker", "stop", cid])
        self.cancel_job()

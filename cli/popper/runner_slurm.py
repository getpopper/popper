import os
import time
import subprocess
import threading

import sh

from popper import utils as pu
from popper import scm
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner
from popper.runner_host import DockerRunner as HostDockerRunner
from popper.runner_host import SingularityRunner as HostSingularityRunner
from popper.runner_host import HostRunner


class SlurmRunner(StepRunner):
    spawned_jobs = set()

    def __init__(self, config):
        super(SlurmRunner, self).__init__(config)

    def __exit__(self, exc_type, exc, traceback):
        SlurmRunner.spawned_jobs = set()

    def _stream_output(self, out_file):
        self.output_stream_pid = set()
        pu.exec_cmd(["tail", "-f", out_file],
                    spawned_processes=self.output_stream_pid)

    def _stream_error(self, err_file):
        self.error_stream_pid = set()
        pu.exec_cmd(["tail", "-f", err_file],
                    spawned_processes=self.error_stream_pid)

    def start_output_error_stream(self, out_file, err_file):
        self.output_stream_thread = threading.Thread(
            target=self._stream_output, args=(out_file,))

        self.error_stream_thread = threading.Thread(
            target=self._stream_error, args=(err_file,))

        self.output_stream_thread.start()
        self.error_stream_thread.start()

    def stop_output_error_stream(self):
        output_stream_proc = list(self.output_stream_pid)[0]
        error_stream_proc = list(self.error_stream_pid)[0]

        output_stream_proc.kill()
        error_stream_proc.kill()

        self.output_stream_thread.join()
        self.error_stream_thread.join()

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

        # start a tail process on the output and error file
        self.start_output_error_stream(out_file, err_file)

        # submit the job and wait, then parse the job_id
        ecode, output = pu.exec_cmd(sbatch_cmd.split(" "), logging=False)
        job_id = int(output.split(" ")[-1].strip("\n"))

        # kill the tail process
        self.stop_output_error_stream()

        SlurmRunner.spawned_jobs.remove(job_name)
        return ecode

    @staticmethod
    def cancel_job():
        for job_name in SlurmRunner.spawned_jobs:
            log.info(f'Cancelling job {job_name}')
            ecode, _ = pu.exec_cmd(["scancel", "--name", job_name])
            if ecode:
                log.fail(f"Failed to cancel the job {job_name}.")


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
        docker_cmd = f"docker build -t {tag} {path} > /dev/null"
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
        SlurmRunner.cancel_job()


class SingularityRunner(SlurmRunner, HostSingularityRunner):
    """Runs actions in singularity."""
    def __init__(self, **kw):
        super(SingularityRunner, self).__init__(**kw)
        if self.config.reuse:
            log.fail('Reuse not supported for SingularityRunner.')

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

    def run(self, step):
        cid = pu.sanitized_name(step["name"], self._config.wid)
        build, img, tag, build_source = self._get_build_info(step)

        cmd = []
        cmd.append(f"rm -rf {os.path.join(self._singularity_cache, cid)}")

        if build:
            cmd.append(f"cd {build_source}")
            cmd.append(f"singularity build {container_path} {recipefile}")

        else:
            cmd.append(f"mkdir -p {os.path.dirname(container_path)}")
            cmd.append(
                f"singularity pull {container_path} {image}")

        if self._config.dry_run:
            return 0

        self._spawned_containers.add(cid)
        ecode = self._submit_batch_job(cmd, step)
        self._spawned_containers.remove(cid)
        return ecode


    # @staticmethod
    # def create_container(cid, step, config):
        # singularity_cache = HostSingularityRunner.setup_singularity_cache(
        #     config.wid)
        # container_path = os.path.join(singularity_cache, cid + '.sif')

        # build, image, build_source = HostDockerRunner.get_build_info(
        #     step, config.workspace_dir, config.workspace_sha)

        # SingularityRunner.singularity_rm(step, container_path, config.dry_run)

        # if build:
        #     SingularityRunner.singularity_build(
        #         step, build_source, container_path, config.dry_run)
        # else:
        #     SingularityRunner.singularity_pull(
        #         step, image, container_path, config.dry_run)

        # return container_path

    # @staticmethod
    # def singularity_rm(step, container_path, dry_run):
    #     if dry_run:
    #         return
    #     step['cmd_list'].append(f"rm -rf {container_path}")

    # @staticmethod
    # def singularity_pull(step, image, container_path, dry_run):
    #     image = "docker://" + image

    #     log.info(f'[{step["name"]}] singularity pull {container_path} {image}')
    #     if dry_run:
    #         return


    # @staticmethod
    # def singularity_build(step, build_source, container_path, dry_run):
    #     cid = os.path.basename(container_path)[:-4]
    #     recipefile = HostSingularityRunner.get_recipe_file(build_source, cid)

    #     log.info(
    #         f'[{step["name"]}] singularity build {container_path} {recipefile}')
    #     if dry_run:
    #         return

        

    @staticmethod
    def singularity_start(step, config, container_path, dry_run):
        env = StepRunner.prepare_environment(step)
        for k, v in env.items():
            os.environ[k] = v

        volumes = [
            f'{config.workspace_dir}:/workspace'
        ]

        args = step.get('args', '')
        runs = step.get('runs', '')
        ecode = None

        if runs:
            info = f'[{step["name"]}] singularity exec {container_path} {runs}'
            commands = runs
            singularity_cmd = f"singularity exec "
        else:
            info = f'[{step["name"]}] singularity run {container_path} {args}'
            commands = args
            singularity_cmd = f"singularity run "

        log.info(info)
        if dry_run:
            return 0

        options = HostSingularityRunner.get_engine_options(step, config)
        for vol in volumes:
            options.append("--bind")
            options.append(vol)

        singularity_cmd += " ".join(options)
        singularity_cmd += f" {container_path}"
        singularity_cmd += f" {' '.join(commands)}"
        step['cmd_list'].append(singularity_cmd)

    def stop_running_tasks(self):
        pass

import os
import threading

from popper import utils as pu
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner
from popper.runner_host import DockerRunner as HostDockerRunner


class SlurmRunner(StepRunner):
    def __init__(self, config):
        super(SlurmRunner, self).__init__(config)

    def __exit__(self, exc_type, exc, traceback):
        self._spawned_jobs = set()

    def _stream_output(self, out_file):
        self.output_stream_pid = set()
        pu.exec_cmd(["tail", "-f", out_file],
                    spawned_processes=self.output_stream_pid)

    def _stream_error(self, err_file):
        self.error_stream_pid = set()
        pu.exec_cmd(["tail", "-f", err_file],
                    spawned_processes=self.error_stream_pid)

    def _start_output_error_stream(self, out_file, err_file):
        self.output_stream_thread = threading.Thread(
            target=self._stream_output, args=(out_file,))

        self.error_stream_thread = threading.Thread(
            target=self._stream_error, args=(err_file,))

        self.output_stream_thread.start()
        self.error_stream_thread.start()

    def _stop_output_error_stream(self):
        output_stream_proc = list(self.output_stream_pid)[0]
        error_stream_proc = list(self.error_stream_pid)[0]

        output_stream_proc.kill()
        error_stream_proc.kill()

        self.output_stream_thread.join()
        self.error_stream_thread.join()

    def _submit_batch_job(self, cmd, step):
        job_name = pu.sanitized_name(step['name'], self.config.wid)
        temp_dir = "/tmp/popper/slurm/"
        os.makedirs(temp_dir, exist_ok=True)

        job_script = os.path.join(temp_dir, f"{job_name}.sh")
        out_file = os.path.join(temp_dir, f"{job_name}.out")
        err_file = os.path.join(temp_dir, f"{job_name}.err")

        # create/truncate log files
        with open(out_file, 'w'):
            pass
        with open(err_file, 'w'):
            pass

        with open(job_script, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(cmd)

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

        # kill the tail process
        self.stop_output_error_stream()

        SlurmRunner.spawned_jobs.remove(job_name)
        return ecode

    def _cancel_job():
        for job_name in self._spawned_jobs:
            log.info(f'Cancelling job {job_name}')
            ecode, _ = pu.exec_cmd(["scancel", "--name", job_name])
            if ecode:
                log.fail(f"Failed to cancel the job {job_name}.")


class DockerRunner(SlurmRunner):

    def __init__(self, config):
        super(DockerRunner, self).__init__(config)
        self._spawned_containers = set()

    def __exit__(self, exc_type, exc, traceback):
        pass

    def run(self, step):
        """Execute the given step in docker."""
        # generate cid
        cid = pu.sanitized_name(step['name'], self.config.wid)
        step['cmd_list'] = []

        build, img, tag, dockerfile = self._get_build_info(step)

        if build:
            self._docker_build(step, img, tag, dockerfile)
        elif not self.config.skip_pull and not step.get('skip_pull', False):
            DockerRunner.docker_pull(step, img, self.config.dry_run)

        # remove container if it exists
        DockerRunner.docker_rm(step, cid, self.config.dry_run)

        # create container
        DockerRunner.docker_create(step, img, cid, self.config)

        if self.config.dry_run:
            return 0

        self._spawned_containers.add(cid)
        DockerRunner.docker_start(step, cid, self.config.dry_run)
        ecode = self.run_script(step)
        self._spawned_containers.remove(cid)
        return ecode

    def run_script(self, step):
        step['cmd_list'] = list(map(lambda x: 'srun ' + x, step['cmd_list']))
        final_cmd = "\n".join(step['cmd_list'])
        return self.submit_batch_job(final_cmd, step)

    @staticmethod
    def docker_create(step, img, cid, config):
        container_args = self._get_container_kwargs(step, img, cid)
        container_args.pop('detach')
        cmd = "docker create "
        cmd += f"--name {container_args.pop('name')} "
        cmd += f"--workdir {container_args.pop('working_dir')} "

        if container_args.get('entrypoint', None):
            cmd += f"--entrypoint {' '.join(container_args.pop('entrypoint'))}"

        # append the vol and envs
        for vol in container_args.pop('volumes'):
            docker_cmd += f"-v {vol} "
        for env_key, env_val in container_args.pop('environment').items():
            docker_cmd += f"-e {env_key}={env_val} "

        image = container_args.pop('image')

        if container_args.get('command', None):
            command = ' '.join(container_args.pop('command'))
        else:
            command = ' '

        for k, v in container_args.items():
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
        self._cancel_job()


#!/usr/bin/python
import ansible.inventory
import ansible.playbook
import ansible.runner
import ansible.constants
from ansible import utils
from ansible import callbacks
import os
import subprocess
import uuid
import boto3

libdir = os.path.join(os.getcwd(), 'local', 'lib')
s3_client = boto3.client('s3')

def run_playbook(**kwargs):

    stats = callbacks.AggregateStats()
    playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
    runner_cb = callbacks.PlaybookRunnerCallbacks(
        stats, verbose=utils.VERBOSITY)

    # use /tmp instead of $HOME
    ansible.constants.DEFAULT_REMOTE_TMP = '/tmp/ansible'

    out = ansible.playbook.PlayBook(
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        stats=stats,
        **kwargs
    ).run()

    return out

def handler(event, context):
    results = []
    for record in event['Records']:

        # Find input/output buckets and key names
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        # Download the raster locally
        download_path = '/tmp/{}{}'.format(uuid.uuid4(), key)
        s3_client.download_file(bucket, key, download_path)

        # Call the worker, setting the environment variables
        command = 'LD_LIBRARY_PATH={} python worker.py "{}"'.format(libdir, download_path)
        #output_path = subprocess.check_output(command, shell=True)

        # Upload the output of the worker to S3
        #s3_client.upload_file(output_path.strip(), output_bucket, output_key)
        #results.append(output_path.strip())

    return main()

def main():
    out = run_playbook(
        playbook=['playbook'],
        inventory=ansible.inventory.Inventory(['localhost'])

    )
    return(out)


if __name__ == '__main__':
    main()

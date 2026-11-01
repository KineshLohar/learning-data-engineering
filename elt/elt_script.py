import os
import subprocess
import time

def wait_for_postgres(host, max_retries=5, delay_seconds=5):
    retries = 0
    while retries < max_retries:
        try:
            result = subprocess.run(
                ["pg_isready", "-h", host], check=True, capture_output=True, text=True)
            if "accepting connections" in result.stdout:
                print(f"Success connecting to {host}")
                return True
        except subprocess.CalledProcessError as e:
            print(f"Error connection to {host}: {e}")
            retries += 1
            print(f"Retrying in {delay_seconds} (attempt {retries})")
            time.sleep(delay_seconds)
    print(f"Max retries reached for {host}")
    return False

# Wait for BOTH databases to be fully up and running
if not wait_for_postgres(host="source_postgres"):
    exit(1)

if not wait_for_postgres(host="destination_postgres"):
    exit(1)

print("STARTING scripts ELT")    

source_config = {
    "dbname": "source_db",
    'user': 'postgres',
    'password': 'secret',
    'host': 'source_postgres'
}

destination_config = {
    "dbname": "destination_db",
    'user': 'postgres',
    'password': 'secret',
    'host': 'destination_postgres'
}

# --- 1. DUMP STEP ---
dump_command = [
    'pg_dump',
    '-h', source_config['host'],
    '-U', source_config['user'],
    '-d', source_config['dbname'],
    '-f', 'data_dump.sql',
    '-w'
]

# FIX: Inherit system environment variables so system binaries are found
dump_env = os.environ.copy()
dump_env['PGPASSWORD'] = source_config['password']

print("Running pg_dump...")
try:
    subprocess.run(dump_command, env=dump_env, check=True, capture_output=True, text=True)
    print("pg_dump completed successfully.")
except subprocess.CalledProcessError as e:
    print("\n❌ !!! PG_DUMP FAILED !!! ❌")
    print("STDOUT:", e.stdout)
    print("STDERR:", e.stderr)
    raise e

# --- 2. LOAD STEP ---
# FIX: Changed '-u' to '-U' and corrected 'data_sump.sql' -> 'data_dump.sql'
load_command = [
    'psql',
    '-h', destination_config['host'],
    '-U', destination_config['user'],
    '-d', destination_config['dbname'],
    '-a', '-f', 'data_dump.sql'
]

# FIX: Inherit system environment variables here as well
load_env = os.environ.copy()
load_env['PGPASSWORD'] = destination_config['password']

print("Running psql load...")
try:
    subprocess.run(load_command, env=load_env, check=True, capture_output=True, text=True)
    print("psql load completed successfully.")
except subprocess.CalledProcessError as e:
    print("\n❌ !!! PSQL LOAD FAILED !!! ❌")
    print("STDOUT:", e.stdout)
    print("STDERR:", e.stderr)
    raise e

print("Ending ELT SCRIPT")

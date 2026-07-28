from datetime import datetime
import subprocess
import time

ADB_PATH = r"C:/Users/1040-G4/Desktop/DEVICE DIAGNOSTIC PROJECT/platform-tools/adb.exe"
report_file = "C:/Users/1040-G4/Desktop/DEVICE DIAGNOSTIC PROJECT/phone_diagnostic_report.txt"

now= datetime.now()
timestamp= now.strftime("%Y-%m-%d %H:%M:%S")
with open(report_file, "w", encoding="utf-8") as f:
    f.write("-------------------------\n")
    f.write("PHONE DIAGNOSTICS REPORT\n")
    f.write("=========================\n")
    f.write(f'Date: {timestamp}\n\n')

def write_to_report(text):
    with open(report_file, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def run_adb_command(command):
    command[0] = ADB_PATH
    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="ignore"
    )
    return result.stdout

def device_connected():
    output = run_adb_command(["adb", "devices"])
    lines = output.strip().split("\n")[1:]

    for line in lines:
        if "device" in line:
            return True

    return False

def device_info():
    write_to_report("==DEVICE INFO==")

    model= run_adb_command(["adb", "shell", "getprop", "ro.product.model"]).strip()
    manufacturer= run_adb_command(["adb", "shell", "getprop", "ro.product.manufacturer"]).strip()
    android_version= run_adb_command(["adb", "shell", "getprop", "ro.build.version.release"]).strip()

    write_to_report(f"Manufacturer: {manufacturer}")
    write_to_report(f"Model: {model}")
    write_to_report(f"Android Version: {android_version}")

def battery_info():
    output = run_adb_command(["adb", "shell", "dumpsys", "battery"])

    level = None
    temp_c = None
    health = None

    for line in output.splitlines():
        line = line.strip()

        # Stop parsing once we reach log sections
        if line.startswith("[") or line == "":
            break

        if line.startswith("level:"):
            try:
                level = int(line.split(":")[1].strip())
            except ValueError:
                level = 0
        elif line.startswith("temperature:"):
            try:
                temp_c = int(line.split(":")[1].strip()) / 10  # deci-degrees → °C
            except ValueError:
                temp_c = 0
        elif line.startswith("health:"):
            health = line.split(":")[1].strip()

    # Safety defaults if values weren't found
    if level is None:
        level = 0
    if temp_c is None:
        temp_c = 0
    if health is None:
        health = "1"

    # Health conversion
    health_map = {
        "1": "UNKNOWN",
        "2": "GOOD",
        "3": "OVERHEAT",
        "4": "DEAD",
        "5": "OVER_VOLTAGE",
        "6": "FAILURE"
    }

    health_status = health_map.get(health, "UNKNOWN")

    # Battery level status
    if level >= 30:
        level_status = "PASS"
    elif level >= 15:
        level_status = "WARNING"
    else:
        level_status = "FAIL"

    # Temperature status
    if temp_c <= 40:
        temp_status = "PASS"
    elif temp_c <= 45:
        temp_status = "WARNING"
    else:
        temp_status = "FAIL"

    # Health status
    health_result = "PASS" if health_status == "GOOD" else "FAIL"

    # Write results to report
    write_to_report("== BATTERY DIAGNOSTIC ==")
    write_to_report(f"Battery Level: {level}% → {level_status}")
    write_to_report(f"Battery Temperature: {temp_c:.1f}°C → {temp_status}")
    write_to_report(f"Battery Health: {health_status} → {health_result}")


def storage_info():
    write_to_report("== STORAGE INFO ==")

    output = run_adb_command(["adb", "shell", "df", "/data"])

    for line in output.splitlines():
        if "/data" in line:
            parts = line.split()
            used_percent = parts[4].replace("%","")

            used_percent = int(used_percent)

            if used_percent < 70:
                status = "PASS"
            elif used_percent <= 90:
                status = "WARNING"
            else:
                status = "FAIL"

            write_to_report(f"Storage Used: {used_percent}% → {status}")

def install_app():
    write_to_report("Installing diagnostic app...")
    run_adb_command(["adb", "install", "diagnostic_app.apk"])



def start_phone_operation():

    install_app()

    run_adb_command(["adb", "logcat", "-c"])

    write_to_report("Launching diagnostic tests...")

    run_adb_command([
        "adb",
        "shell",
        "am",
        "start",
        "-n",
        "com.diagnostic.test/.MainActivity"
    ])

    write_to_report("Collecting test results...")
    
    process = subprocess.Popen(
        [ADB_PATH, "logcat"],
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    start_time = time.time()
    timeout = 60   # seconds

    for line in process.stdout:

        if "TEST_RESULT" in line:
            write_to_report(line.strip())

        if "ALL_TEST_COMPLETE" in line:
            break

        if time.time() - start_time > timeout:
            write_to_report("Test timeout reached.")
            break

    process.terminate()
    process.wait()
    write_to_report("Removing diagnostic app...")
    run_adb_command(["adb", "uninstall", "com.diagnostic.test"])


def run_diagnostics():
    write_to_report("----------------------------------")
    write_to_report("Phone detected")

    device_info()

    write_to_report("----------------------------------")
    storage_info()

    write_to_report("----------------------------------")
    battery_info()

    write_to_report("----------------------------------")
    start_phone_operation()


def main():
    if device_connected():
        run_diagnostics()
    else:
        write_to_report("Waiting for device connection...")

        timeout = 30
        start_time = time.time()

        while time.time() - start_time < timeout:

            if device_connected():
                run_diagnostics()
                return

            write_to_report("No device yet... checking again in 10 seconds")
            time.sleep(10)

        write_to_report("No device detected after 30 seconds")

main()

123443442